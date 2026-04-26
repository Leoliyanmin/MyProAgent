from typing import Dict, Any, List, Optional
import json


EXTRACT_PROMPT = """你是一位用户画像分析师。请根据以下用户的对话内容，分析用户的兴趣领域和技能。

用户消息：{}

返回 JSON 格式（不要包含其他文字）：
{{
  "interests": ["兴趣1", "兴趣2"],
  "skills": ["技能1", "技能2"]
}}

要求：
- interests：用户对话中体现的兴趣话题，最多3个
- skills：用户对话中体现的技能，最多3个
- 如果无法推断，列表可以为空 []
- 每个词不超过10个字
"""


class ProfileExtractor:

    def __init__(self, llm_provider=None):
        self.llm_provider = llm_provider

    async def extract_from_interaction(self, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        profile_update = {
            "interests_identified": await self._extract_interests(interaction_data),
            "skills_demonstrated": await self._extract_skills(interaction_data),
            "preferences_inferred": self._extract_preferences(interaction_data),
            "study_work_patterns": self._extract_patterns(interaction_data),
            "personality_indicators": self._extract_personality(interaction_data)
        }
        return profile_update

    async def _extract_interests(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        message = data.get("user_input", {}).get("raw_message", "")
        if not message.strip() or not self.llm_provider:
            return []

        print(f"[ProfileExtractor] 正在调用 LLM 分析兴趣领域...")
        prompt = EXTRACT_PROMPT.format(message)
        messages = [{"role": "user", "content": prompt}]

        try:
            response = await self.llm_provider.chat(messages)
            content = response.content or ""
            result = self._parse_json_response(content)
            if result and "interests" in result:
                interests = result["interests"]
                if isinstance(interests, list):
                    topics = [t for t in interests[:3] if isinstance(t, str) and t.strip()]
                    print(f"[ProfileExtractor] 兴趣分析完成: {topics}")
                    return [
                        {"topic": topic, "confidence": 0.8, "source": "llm_inferred"}
                        for topic in topics
                    ]
            print(f"[ProfileExtractor] 兴趣分析完成: 无结果")
        except Exception as e:
            print(f"[ProfileExtractor] LLM interests error: {e}")

        return []

    async def _extract_skills(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        message = data.get("user_input", {}).get("raw_message", "")
        if not message.strip() or not self.llm_provider:
            return []

        print(f"[ProfileExtractor] 正在调用 LLM 分析技能标签...")
        prompt = EXTRACT_PROMPT.format(message)
        messages = [{"role": "user", "content": prompt}]

        try:
            response = await self.llm_provider.chat(messages)
            content = response.content or ""
            result = self._parse_json_response(content)
            if result and "skills" in result:
                skills = result["skills"]
                if isinstance(skills, list):
                    skill_list = [s for s in skills[:3] if isinstance(s, str) and s.strip()]
                    print(f"[ProfileExtractor] 技能分析完成: {skill_list}")
                    return [
                        {"skill": skill, "level": "intermediate", "evidence": "llm_inferred"}
                        for skill in skill_list
                    ]
            print(f"[ProfileExtractor] 技能分析完成: 无结果")
        except Exception as e:
            print(f"[ProfileExtractor] LLM skills error: {e}")

        return []

    def _parse_json_response(self, content: str) -> Optional[Dict[str, Any]]:
        import re
        json_match = re.search(r'\{[^}]+\}', content, re.DOTALL)
        if not json_match:
            return None
        try:
            return json.loads(json_match.group())
        except (json.JSONDecodeError, ValueError):
            return None

    def _extract_preferences(self, data: Dict[str, Any]) -> Dict[str, Any]:
        message = data.get("user_input", {}).get("raw_message", "")
        response_length = data.get("agent_output", {}).get("response_length", 0)

        preferences = {
            "communication_style": "casual",
            "response_length_preference": "medium",
            "preferred_language": "zh",
            "preferred_tool_usage": "automatic"
        }

        formal_keywords = ["请", "麻烦", "请问", "谢谢"]
        if any(kw in message for kw in formal_keywords):
            preferences["communication_style"] = "formal"

        casual_keywords = ["帮我", "搞一下", "搞定"]
        if any(kw in message for kw in casual_keywords):
            preferences["communication_style"] = "casual"

        if response_length < 100:
            preferences["response_length_preference"] = "short"
        elif response_length > 500:
            preferences["response_length_preference"] = "long"

        return preferences

    def _extract_patterns(self, data: Dict[str, Any]) -> Dict[str, Any]:
        intent = data.get("user_input", {}).get("intent_category", "")
        message = data.get("user_input", {}).get("raw_message", "")
        timestamp = data.get("metadata", {}).get("timestamp", "")

        patterns = {
            "topic_areas": [],
            "typical_task_types": [],
            "active_hours": [],
            "work_style": "flexible"
        }

        topic_mapping = {
            "task_delegation": ["任务管理"],
            "file_operation": ["文件管理"],
            "schedule_management": ["日程安排"],
            "study_plan": ["学习"],
            "social": ["社交"]
        }

        if intent in topic_mapping:
            patterns["topic_areas"].extend(topic_mapping[intent])

        task_type_mapping = {
            "task_delegation": ["委托任务"],
            "file_operation": ["文件操作"],
            "schedule_management": ["日程管理"]
        }

        if intent in task_type_mapping:
            patterns["typical_task_types"].extend(task_type_mapping[intent])

        if timestamp:
            try:
                hour = int(timestamp.split("T")[1].split(":")[0])
                if 6 <= hour < 12:
                    patterns["active_hours"].append("morning")
                elif 12 <= hour < 18:
                    patterns["active_hours"].append("afternoon")
                elif 18 <= hour < 22:
                    patterns["active_hours"].append("evening")
            except (IndexError, ValueError):
                pass

        if any(kw in message for kw in ["计划", "安排", "按时"]):
            patterns["work_style"] = "structured"
        elif any(kw in message for kw in [" deadline", "截止"]):
            patterns["work_style"] = "deadline_driven"

        return patterns

    def _extract_personality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        message = data.get("user_input", {}).get("raw_message", "")
        preferences = data.get("user_profile_update", {}).get("preferences_inferred", {})

        personality = {
            "detail_oriented": 0.5,
            "proactive": 0.5,
            "collaborative": 0.5
        }

        detail_keywords = ["具体", "详细", "细节", "准确"]
        if any(kw in message for kw in detail_keywords):
            personality["detail_oriented"] = 0.8

        proactive_keywords = ["主动", "提前", "预先", "下次"]
        if any(kw in message for kw in proactive_keywords):
            personality["proactive"] = 0.8

        collaborative_keywords = ["一起", "合作", "帮", "我们"]
        if any(kw in message for kw in collaborative_keywords):
            personality["collaborative"] = 0.8

        return personality
