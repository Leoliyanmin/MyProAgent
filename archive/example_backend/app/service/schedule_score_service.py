from sqlalchemy.orm import Session
from typing import List, Dict, Any, Tuple
from model.entities import Schedule, User
from service import ai_service
import re
import json

# =============================================================
# Schedule AI Scoring Service
# 修改: 由原来的纯启发式得分改为优先使用 AI 评估打分 (返回 JSON),
#       若 AI JSON 解析失败则回退到启发式算法。理想工作:生活 = 4:1 (80% 工作时间)
# =============================================================

WORK_TYPES = {"course", "class", "lecture", "lab", "exam", "work", "study"}

SPLIT_PATTERN = re.compile(r"[,;，；、\s]+")

def _fetch_user_and_schedule(db: Session, user_id: int) -> tuple[User | None, List[Schedule]]:
    user = db.get(User, user_id)
    schedules: List[Schedule] = []
    if user:
        schedules = user.schedules
    return user, schedules

def _compute_durations(schedules: List[Schedule]) -> Dict[str, Any]:
    work_minutes = 0
    life_minutes = 0
    details: List[Dict[str, Any]] = []
    for sch in schedules:
        if not sch.start_time or not sch.end_time:
            continue
        duration = (sch.end_time.hour * 60 + sch.end_time.minute) - (sch.start_time.hour * 60 + sch.start_time.minute)
        kind = "work" if (sch.schedule_type or "").lower() in WORK_TYPES else "life"
        if kind == "work":
            work_minutes += duration
        else:
            life_minutes += duration
        details.append({
            "id": sch.schedule_id,
            "name": sch.name,
            "type": sch.schedule_type,
            "weekday": sch.weekday,
            "start": sch.start_time.strftime("%H:%M") if sch.start_time else None,
            "end": sch.end_time.strftime("%H:%M") if sch.end_time else None,
            "duration_minutes": duration,
            "category": kind
        })
    total_minutes = work_minutes + life_minutes
    return {
        "work_minutes": work_minutes,
        "life_minutes": life_minutes,
        "total_minutes": total_minutes,
        "details": details
    }

def _score_work_life(work_minutes: int, life_minutes: int) -> int:
    """启发式工作-生活得分 (用于 AI 回退)。"""
    total = work_minutes + life_minutes
    if total == 0:
        return 0
    ratio = work_minutes / total
    ideal = 0.8  # 4:1
    raw = 1 - (abs(ratio - ideal) / ideal)
    score = max(0, min(100, round(raw * 100)))
    return score

def _extract_interest_keywords(interest: str | None) -> List[str]:
    if not interest:
        return []
    parts = [p.strip().lower() for p in SPLIT_PATTERN.split(interest) if p.strip()]
    # remove too short tokens
    return [p for p in parts if len(p) > 1]

def _score_interest_alignment(schedules: List[Schedule], keywords: List[str]) -> tuple[int, List[str]]:
    if not schedules or not keywords:
        return 0, []
    matched_names: List[str] = []
    for sch in schedules:
        haystack = f"{sch.name} {sch.description or ''}".lower()
        if any(k in haystack for k in keywords):
            matched_names.append(sch.name)
    alignment = (len(matched_names) / len(schedules)) * 100 if schedules else 0
    return round(alignment), matched_names

def _build_ai_scoring_messages(user_name: str, interest_keywords: List[str], durations: Dict[str, Any], heuristic_scores: Dict[str, int]) -> List[Dict[str, str]]:
    """构造给 LLM 的打分与建议消息。要求 LLM 返回 JSON。"""
    summary_lines = [
        f"{d['name']}|{d['category']}|{d['weekday']}|{d['start']}-{d['end']}|{d['duration_minutes']}min|{d['type']}"
        for d in durations["details"]
    ]
    schedule_table = "\n".join(summary_lines[:60])  # 安全截断
    interests_str = ", ".join(interest_keywords) if interest_keywords else "(未填写兴趣)"
    system = (
        "你是一名大学生日程与兴趣评估专家。请依据日程项和兴趣关键词为学生的日程做量化评分并给出建议。"
        "严格输出一个 JSON，不要解释，不要额外文本。键: work_life_balance_score, interest_alignment_score, total_score, advice。"
        "评分规则: 工作:生活 理想比例约 4:1 (工作 80% 时间)。若工作占比过高或过低均扣分。"
        "兴趣匹配: 若日程名称或描述包含兴趣关键词，得分提高；匹配比例与深度 (多样性、分散到不同天) 可略作主观调整。"
        "综合得分你可按权重 0.6*工作生活 + 0.4*兴趣，也可在极端情况下做≤5分微调。"
        "所有分数为 0-100 的整数。advice 为一句英文，给出 1-2 条具体可执行优化建议，积极、具体、避免陈词滥调。"
        "如果无法合理评分返回一个你认为最合理的估计，不要返回空。"
    )
    user_content = (
        f"学生姓名: {user_name}\n"
        f"兴趣关键词: {interests_str}\n"
        f"启发式初始分: 工作生活={heuristic_scores['work_life']} 兴趣匹配={heuristic_scores['interest']} 综合={heuristic_scores['total']}\n"
        f"日程数据列 (name|category|weekday|start-end|duration|type):\n{schedule_table}\n"
        "请直接输出 JSON。"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user_content}
    ]

def _parse_ai_json(text: str) -> Dict[str, Any] | None:
    """尝试从模型输出中解析 JSON (容忍代码块和多余文本)。"""
    if not text:
        return None
    # 去除 ```json / ``` 包裹
    if "```" in text:
        # 优先定位 json 代码块
        if "```json" in text:
            try:
                segment = text.split("```json", 1)[1].split("```", 1)[0]
                text = segment.strip()
            except Exception:
                pass
        else:
            # 任意代码块
            try:
                segment = text.split("```", 1)[1].split("```", 1)[0]
                text = segment.strip()
            except Exception:
                pass
    # 使用正则截取第一个 { ... }
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        candidate = match.group(0)
        try:
            return json.loads(candidate)
        except Exception:
            pass
    # 直接尝试整体解析
    try:
        return json.loads(text)
    except Exception:
        return None

def _ai_score(user_name: str, interest_keywords: List[str], durations: Dict[str, Any], heuristic_scores: Dict[str, int], model_name: str) -> Tuple[Dict[str, int], str, Dict[str, Any]]:
    """调用 LLM 获取 AI 评分; 返回 (scores_dict, advice_text, raw_json)."""
    messages = _build_ai_scoring_messages(user_name, interest_keywords, durations, heuristic_scores)
    output = ai_service.get_completion(messages, model=model_name)
    parsed = _parse_ai_json(output)
    if not parsed:
        return heuristic_scores, "(AI解析失败，使用启发式建议)" + output[:100], {"raw_text": output}
    # 规范化
    def _clamp_int(val, default=0):
        try:
            return max(0, min(100, int(round(float(val)))))
        except Exception:
            return default
    scores = {
        "work_life_balance_score": _clamp_int(parsed.get("work_life_balance_score", heuristic_scores["work_life"])),
        "interest_alignment_score": _clamp_int(parsed.get("interest_alignment_score", heuristic_scores["interest"])),
        "total_score": _clamp_int(parsed.get("total_score", heuristic_scores["total"]))
    }
    advice = parsed.get("advice") or "(AI未提供建议)"
    return scores, advice, parsed

def score_schedule(db: Session, user_id: int, llm: str | None = None) -> Dict[str, Any]:
    """对用户当前日程进行 AI 评分 (JSON) + 建议，解析失败回退启发式。"""
    user, schedules = _fetch_user_and_schedule(db, user_id)
    if not user:
        return {"error": "用户不存在"}

    durations = _compute_durations(schedules)
    interest_keywords = _extract_interest_keywords(user.interest)
    heuristic_work_life = _score_work_life(durations["work_minutes"], durations["life_minutes"])
    heuristic_interest, matched_events = _score_interest_alignment(schedules, interest_keywords)
    heuristic_total = round(heuristic_work_life * 0.6 + heuristic_interest * 0.4)
    heuristic_scores = {
        "work_life": heuristic_work_life,
        "interest": heuristic_interest,
        "total": heuristic_total
    }

    model_name = llm or "gpt-4o-mini"
    ai_scores, advice, raw_json = _ai_score(user.name, interest_keywords, durations, heuristic_scores, model_name)

    return {
        "user_id": user.user_id,
        "user_name": user.name,
        "work_life_balance_score": ai_scores["work_life_balance_score"],
        "interest_alignment_score": ai_scores["interest_alignment_score"],
        "total_score": ai_scores["total_score"],
        "work_minutes": durations["work_minutes"],
        "life_minutes": durations["life_minutes"],
        "interest_keywords": interest_keywords,
        "matched_events": matched_events,
        "schedule_items": durations["details"],
        "advice": advice,
        "debug": {
            "heuristic": heuristic_scores,
            "raw_ai": raw_json
        }
    }
