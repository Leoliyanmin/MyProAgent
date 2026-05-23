import json
import logging
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

localagent_path = Path(__file__).parent.parent.parent / "localagent"
if str(localagent_path) not in sys.path:
    sys.path.insert(0, str(localagent_path))

from service.email_service import EmailService
from service.schedule_service import ScheduleService
from service.agent_service import AgentService

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are an email priority analysis assistant. Analyze the user's emails in the context of their "
    "profile and upcoming schedule to identify the 5 most important emails.\n\n"
    "Scoring criteria:\n"
    "- Relevance to user's interests and skills (courses, projects, research)\n"
    "- Relevance to upcoming schedule events (exams, meetings, deadlines)\n"
    "- Sender importance (advisor, professor, course staff)\n"
    "- Urgency (approaching deadlines, time-sensitive content)\n\n"
    "Return ONLY valid JSON (no markdown code blocks, no extra text):\n"
    '{"rankings": [{"id": <number>, "score": <0-100>, "reason": "<reason in Chinese>"}, ...]}'
)

RULE_SENDER_KEYWORDS = [
    "导师", "教授", "老师", "advisor", "professor", "instructor",
    "教务", "院长", "系主任", "辅导员",
]

RULE_COURSE_PATTERNS = [
    r"c[sm]\d{3}", r"\d{4}", r"课程", r"作业", r"assignment", r"exam",
    r"考试", r"project", r"论文", r"thesis", r"毕业设计",
]


class EmailPriorityService:
    def __init__(self):
        self.email_service = EmailService()
        self.schedule_service = ScheduleService()

    async def prioritize(self, user_id: str) -> dict:
        emails_result = self.email_service.get_email_messages(user_id)
        if not emails_result.get("success"):
            return {"success": False, "message": "获取邮件列表失败"}
        emails = emails_result.get("messages", [])
        if not emails:
            return {"success": True, "prioritized": [], "strategy_used": "none", "message": "没有邮件可分析"}

        emails = emails[:30]

        profile = AgentService().get_user_profile(user_id)
        schedules_result = self.schedule_service.get_schedules(user_id)
        schedules = schedules_result.get("schedules", []) if schedules_result.get("success") else []
        upcoming = self._filter_upcoming_schedules(schedules)

        try:
            result = await self._llm_rank(emails, profile, upcoming)
            result["strategy_used"] = "llm"
        except Exception as e:
            logger.warning(f"LLM ranking failed, fallback to rule: {e}")
            result = self._rule_rank(emails, profile, upcoming)
            result["strategy_used"] = "rule"

        prioritized = result.get('prioritized', [])
        if prioritized:
            try:
                from local_backend.database.code.operations.database_email_v2_operations import StarredEmailV2Operations
                star_ops = StarredEmailV2Operations()
                all_starred = star_ops.list_starred(user_id)
                ai_starred_ids = {s['email_id'] for s in all_starred if s.get('source') == 'ai'}
                new_ai_ids = {item['id'] for item in prioritized}
                for email_id in ai_starred_ids - new_ai_ids:
                    star_ops.remove_star(user_id, email_id)
                for item in prioritized:
                    if item['id'] not in ai_starred_ids:
                        star_ops.add_star(user_id, item['id'], item.get('reason', ''), 'ai')
            except Exception as e:
                logger.warning(f"Failed to persist AI prioritized emails: {e}")

        return result

    async def _llm_rank(
        self, emails: list[dict], profile: dict, schedules: list[dict]
    ) -> dict:
        provider = AgentService().agent.provider
        user_prompt = self._build_llm_prompt(emails, profile, schedules)

        response = await provider.chat(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ]
        )

        raw = response.content or ""
        rankings = self._parse_llm_response(raw)
        if not rankings:
            raise ValueError("Failed to parse LLM response")

        ranked = sorted(rankings, key=lambda x: x.get("score", 0), reverse=True)[:5]
        prioritized = [
            {"id": r["id"], "reason": r.get("reason", "")}
            for r in ranked
        ]
        return {"success": True, "prioritized": prioritized}

    def _build_llm_prompt(self, emails: list[dict], profile: dict, schedules: list[dict]) -> str:
        interests = [i.get("topic", "") for i in profile.get("interests_identified", [])]
        skills = [s.get("skill", "") for s in profile.get("skills_demonstrated", [])]
        mbti = profile.get("mbti_inference", {}).get("mbti_type", "")
        work_style = profile.get("preferences_inferred", {}).get("communication_style", "")

        profile_lines = [
            f"- 兴趣领域: {interests}",
            f"- MBTI: {mbti}",
            f"- 技能: {skills}",
            f"- 沟通风格: {work_style}",
        ]

        now = datetime.now()
        schedule_lines = []
        for s in schedules:
            title = s.get("schedule_title", "")
            start = s.get("schedule_start_time", "")
            priority = s.get("schedule_priority", 2)
            schedule_lines.append(f"  - [{start}] {title} (优先级: {priority})")
        if not schedule_lines:
            schedule_lines.append("  (无近期日程)")

        email_lines = []
        for e in emails:
            eid = e.get("id", "")
            sender = e.get("sender", "")
            title = e.get("title", "")
            time = e.get("release_time", "")
            ctx = (e.get("context", "") or "")[:120].replace("\n", " ")
            email_lines.append(f"  [{eid}] 发件人: {sender} | 主题: {title} | 时间: {time}")
            email_lines.append(f"      摘要: {ctx}")

        return (
            "用户画像：\n"
            + "\n".join(profile_lines)
            + "\n\n近期日程：\n"
            + "\n".join(schedule_lines)
            + f"\n\n邮件列表（共 {len(emails)} 封）：\n"
            + "\n".join(email_lines)
            + "\n\n请分析以上邮件，输出最重要的 5 封。"
        )

    def _parse_llm_response(self, raw: str) -> list[dict] | None:
        json_match = re.search(r"\{[\s\S]*\}", raw)
        if not json_match:
            return None
        try:
            data = json.loads(json_match.group())
            rankings = data.get("rankings", data.get("prioritized", []))
            if isinstance(rankings, list) and len(rankings) > 0:
                return rankings
        except (json.JSONDecodeError, TypeError):
            pass
        return None

    def _rule_rank(self, emails: list[dict], profile: dict, schedules: list[dict]) -> dict:
        interests = [i.get("topic", "").lower() for i in profile.get("interests_identified", [])]
        skills = [s.get("skill", "").lower() for s in profile.get("skills_demonstrated", [])]
        schedule_titles = [s.get("schedule_title", "").lower() for s in schedules]
        now = datetime.now()

        scored = []
        for e in emails:
            score = 0
            reasons = []

            title = (e.get("title") or "") + " " + (e.get("context") or "")
            title_lower = title.lower()
            sender = (e.get("sender") or "").lower()

            for kw in RULE_SENDER_KEYWORDS:
                if kw.lower() in sender:
                    score += 30
                    reasons.append(f"关键发件人: {kw}")
                    break

            for interest in interests:
                if interest and interest in title_lower:
                    score += 15
                    reasons.append(f"匹配兴趣: {interest}")

            for skill in skills:
                if skill and skill in title_lower:
                    score += 15
                    reasons.append(f"匹配技能: {skill}")

            for st in schedule_titles:
                words = set(st.split())
                email_words = set(title_lower.split())
                common = words & email_words
                if common:
                    score += 20 * len(common)
                    reasons.append(f"匹配日程: {', '.join(list(common)[:2])}")

            time_str = e.get("release_time", "")
            if time_str:
                try:
                    email_time = datetime.fromisoformat(time_str.replace("Z", "+00:00").split(".")[0])
                    email_time = email_time.replace(tzinfo=None)
                    days_diff = (now - email_time).days
                    if days_diff <= 3:
                        score += 15
                    elif days_diff <= 7:
                        score += 10
                    elif days_diff <= 14:
                        score += 5
                except (ValueError, TypeError):
                    pass

            if score > 0:
                scored.append({"id": e.get("id"), "score": score, "reason": "; ".join(reasons[:3])})

        scored.sort(key=lambda x: x["score"], reverse=True)
        prioritized = scored[:5]

        return {"success": True, "prioritized": prioritized}

    @staticmethod
    def _filter_upcoming_schedules(schedules: list[dict]) -> list[dict]:
        now = datetime.now()
        cutoff = now + timedelta(days=7)
        filtered = []
        for s in schedules:
            start_str = s.get("schedule_start_time", "")
            if not start_str:
                continue
            try:
                start = datetime.fromisoformat(start_str.replace("Z", "+00:00").split(".")[0])
                start = start.replace(tzinfo=None)
                if now <= start <= cutoff:
                    filtered.append(s)
            except (ValueError, TypeError):
                pass
        return filtered
