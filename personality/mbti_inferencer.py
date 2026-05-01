from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import json


@dataclass
class MBTIScore:
    E: float = 0.5
    I: float = 0.5
    S: float = 0.5
    N: float = 0.5
    T: float = 0.5
    F: float = 0.5
    J: float = 0.5
    P: float = 0.5


MBTI_SCORE_PROMPT = """你是一位专业的 MBTI 人格分析专家。请根据以下用户的对话记录，对 MBTI 八个维度分别评分（1-5分）。

评分规则：
- 每个维度独立评分，1 表示极低倾向，5 表示极高倾向
- E（外向）和 I（内向）是同一维度的两端，请分别评分
- S（实感）和 N（直觉）是同一维度的两端，请分别评分
- T（理性）和 F（情感）是同一维度的两端，请分别评分
- J（判断）和 P（感知）是同一维度的两端，请分别评分

用户对话记录：
{}

请严格按照以下 JSON 格式返回，不要包含其他文字：
{{"E": 分数, "I": 分数, "S": 分数, "N": 分数, "T": 分数, "F": 分数, "J": 分数, "P": 分数}}

注意：分数必须为 1-5 之间的整数。"""


class MBTIInferencer:

    def __init__(self, llm_provider=None):
        self.llm_provider = llm_provider

    async def infer_mbti(self, user_profile: Dict[str, Any], raw_messages: List[str] = None) -> Dict[str, Any]:
        score = MBTIScore()

        if raw_messages and self.llm_provider:
            score = await self._llm_analyze(raw_messages, score)

        score = self._analyze_energy_source(user_profile, score)
        score = self._analyze_information_gathering(user_profile, score)
        score = self._analyze_decision_making(user_profile, score)
        score = self._analyze_lifestyle(user_profile, score)

        mbti_type = self._calculate_mbti_type(score)

        return {
            "mbti_type": mbti_type,
            "scores": {
                "E_I": {"E": round(score.E, 3), "I": round(score.I, 3)},
                "S_N": {"S": round(score.S, 3), "N": round(score.N, 3)},
                "T_F": {"T": round(score.T, 3), "F": round(score.F, 3)},
                "J_P": {"J": round(score.J, 3), "P": round(score.P, 3)}
            },
            "confidence": self._calculate_confidence(score),
            "description": self._get_mbti_description(mbti_type)
        }

    async def _llm_analyze(self, raw_messages: List[str], score: MBTIScore) -> MBTIScore:
        all_text = "\n".join(raw_messages[-20:])
        if not all_text.strip():
            return score

        print(f"[MBTIInferencer] 正在调用 LLM 进行 MBTI 维度评分...")
        prompt = MBTI_SCORE_PROMPT.format(all_text)
        messages = [{"role": "user", "content": prompt}]

        try:
            response = await self.llm_provider.chat(messages)
            content = response.content or ""
            scores = self._parse_llm_response(content)
            if scores:
                print(f"[MBTIInferencer] MBTI 各维度评分: E={scores.get('E')} I={scores.get('I')} S={scores.get('S')} N={scores.get('N')} T={scores.get('T')} F={scores.get('F')} J={scores.get('J')} P={scores.get('P')}")
                score.E = max(0.05, min(0.95, scores.get("E", 3) / 5.0))
                score.I = max(0.05, min(0.95, scores.get("I", 3) / 5.0))
                score.S = max(0.05, min(0.95, scores.get("S", 3) / 5.0))
                score.N = max(0.05, min(0.95, scores.get("N", 3) / 5.0))
                score.T = max(0.05, min(0.95, scores.get("T", 3) / 5.0))
                score.F = max(0.05, min(0.95, scores.get("F", 3) / 5.0))
                score.J = max(0.05, min(0.95, scores.get("J", 3) / 5.0))
                score.P = max(0.05, min(0.95, scores.get("P", 3) / 5.0))
            else:
                print(f"[MBTIInferencer] LLM 返回结果解析失败")
        except Exception as e:
            print(f"[MBTIInferencer] LLM analyze error: {e}")

        return score

    def _parse_llm_response(self, content: str) -> Optional[Dict[str, int]]:
        import re
        json_match = re.search(r'\{[^}]+\}', content, re.DOTALL)
        if not json_match:
            return None
        try:
            data = json.loads(json_match.group())
            required = ["E", "I", "S", "N", "T", "F", "J", "P"]
            if all(k in data for k in required):
                return {k: max(1, min(5, int(data[k]))) for k in required}
        except (json.JSONDecodeError, ValueError, TypeError):
            pass
        return None

    def _analyze_energy_source(self, profile: Dict[str, Any], score: MBTIScore) -> MBTIScore:
        interactions = profile.get("interaction_count", 0)
        social_interactions = profile.get("social_interaction_count", 0)
        collaborative_tasks = profile.get("collaborative_task_count", 0)

        if interactions > 0:
            social_ratio = (social_interactions + collaborative_tasks) / interactions
            score.E = min(1.0, score.E + social_ratio * 0.3)
            score.I = max(0.0, score.I - social_ratio * 0.15)

        return score

    def _analyze_information_gathering(self, profile: Dict[str, Any], score: MBTIScore) -> MBTIScore:
        return score

    def _analyze_decision_making(self, profile: Dict[str, Any], score: MBTIScore) -> MBTIScore:
        personality = profile.get("personality_indicators", {})
        detail_oriented = personality.get("detail_oriented", 0.5)
        collaborative = personality.get("collaborative", 0.5)

        score.T = min(1.0, score.T + detail_oriented * 0.3)
        score.F = max(0.0, score.F - detail_oriented * 0.15)
        score.F = min(1.0, score.F + collaborative * 0.2)
        score.T = max(0.0, score.T - collaborative * 0.1)

        return score

    def _analyze_lifestyle(self, profile: Dict[str, Any], score: MBTIScore) -> MBTIScore:
        patterns = profile.get("study_work_patterns", {})
        work_style = patterns.get("work_style", "flexible")

        if work_style == "structured":
            score.J = min(1.0, score.J + 0.3)
            score.P = max(0.0, score.P - 0.15)
        elif work_style == "deadline_driven":
            score.J = min(1.0, score.J + 0.2)
            score.P = max(0.0, score.P - 0.1)
        elif work_style == "flexible":
            score.P = min(1.0, score.P + 0.2)
            score.J = max(0.0, score.J - 0.1)

        return score

    def _calculate_mbti_type(self, score: MBTIScore) -> str:
        mbti = ""
        mbti += "E" if score.E > score.I else "I"
        mbti += "S" if score.S > score.N else "N"
        mbti += "T" if score.T > score.F else "F"
        mbti += "J" if score.J > score.P else "P"
        return mbti

    def _calculate_confidence(self, score: MBTIScore) -> float:
        dimensions = [
            abs(score.E - score.I),
            abs(score.S - score.N),
            abs(score.T - score.F),
            abs(score.J - score.P)
        ]
        confidence = sum(dimensions) / (4 * 0.5)
        return round(min(1.0, max(0.0, confidence)), 3)

    def _get_mbti_description(self, mbti_type: str) -> str:
        descriptions = {
            "INTJ": "建筑师型 - 独立、战略性思考者，善于制定长期计划",
            "INTP": "逻辑学家型 - 好奇、分析型思考者，喜欢探索理论",
            "ENTJ": "指挥官型 - 果断、有领导力的组织者",
            "ENTP": "辩论家型 - 聪明、好奇的思想家，喜欢挑战",
            "INFJ": "提倡者型 - 理想主义、有洞察力的指导者",
            "INFP": "调停者型 - 诗意、善良的理想主义者",
            "ENFJ": "主人公型 - 有魅力、鼓舞人心的领导者",
            "ENFP": "竞选者型 - 热情、有创造力的自由精神",
            "ISTJ": "物流师型 - 实际、注重事实的可靠者",
            "ISFJ": "守卫者型 - 专注、温暖的保护者",
            "ESTJ": "总经理型 - 出色的管理者，注重秩序",
            "ESFJ": "执政官型 - 关心他人、善于社交的合作者",
            "ISTP": "鉴赏家型 - 大胆、实际的实验者",
            "ISFP": "探险家型 - 灵活、有魅力的艺术家",
            "ESTP": "企业家型 - 聪明、精力充沛的实干家",
            "ESFP": "表演者型 - 自发、精力充沛的娱乐者"
        }
        return descriptions.get(mbti_type, "未知类型")
