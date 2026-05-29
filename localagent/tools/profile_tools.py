"""Profile tool for LocalAgent - reads user profile data from AI analysis."""

from __future__ import annotations

from typing import Callable

from .base import BaseTool


class GetUserProfileTool(BaseTool):
    """Read the user's AI-inferred profile (MBTI, interests, skills, personality)."""

    name = "get_user_profile"
    description = (
        "Get your personal profile data including MBTI personality type, "
        "interests, skills, work patterns, and personality indicators "
        "inferred by AI analysis. Use this when the user asks about their "
        "personality, MBTI type, interests, skills, or what kind of person "
        "they are."
    )
    parameters = {
        "type": "object",
        "properties": {},
        "required": [],
    }

    def __init__(self, profile_getter: Callable[[], dict]):
        self._profile_getter = profile_getter

    async def execute(self, **kwargs) -> str:
        profile = self._profile_getter()
        if not profile or not any(
            profile.get(k)
            for k in (
                "mbti_inference",
                "interests_identified",
                "skills_demonstrated",
            )
        ):
            return (
                "No profile data available yet. Use the app more and interact "
                "with the agent so the AI can analyze your personality over time."
            )

        lines = ["## User Profile Analysis"]

        mbti = profile.get("mbti_inference", {})
        if mbti and mbti.get("mbti_type"):
            lines.append(f"**MBTI Type**: {mbti['mbti_type']}")
            desc = mbti.get("description")
            if desc:
                lines.append(f"**Description**: {desc}")
            scores = mbti.get("scores", {})
            if scores:
                lines.append("**Dimension Scores**:")
                for dim_pair, sub_scores in scores.items():
                    if isinstance(sub_scores, dict):
                        parts = ", ".join(
                            f"{k}: {v:.0%}" for k, v in sub_scores.items()
                        )
                        lines.append(f"  - {dim_pair}: {parts}")
                    else:
                        lines.append(f"  - {dim_pair}: {sub_scores:.0%}")
            if mbti.get("confidence"):
                lines.append(f"**MBTI Confidence**: {mbti['confidence']:.0%}")
            lines.append("")

        interests = profile.get("interests_identified", [])
        if interests:
            lines.append("**Interests**:")
            for i in interests:
                topic = i.get("topic", "")
                score = i.get("score", "")
                if score:
                    lines.append(f"  - {topic} (score: {score})")
                else:
                    lines.append(f"  - {topic}")
            lines.append("")

        skills = profile.get("skills_demonstrated", [])
        if skills:
            lines.append("**Skills**:")
            for s in skills:
                skill = s.get("skill", "")
                level = s.get("level", "")
                if level:
                    lines.append(f"  - {skill} ({level})")
                else:
                    lines.append(f"  - {skill}")
            lines.append("")

        prefs = profile.get("preferences_inferred", {})
        if prefs:
            lines.append("**Communication Preferences**:")
            mapping = {
                "communication_style": "Style",
                "response_length_preference": "Response length",
                "preferred_language": "Language",
                "preferred_tool_usage": "Tool usage",
            }
            for key, val in prefs.items():
                label = mapping.get(key, key)
                lines.append(f"  - {label}: {val}")
            lines.append("")

        patterns = profile.get("study_work_patterns", {})
        if patterns:
            topic_areas = patterns.get("topic_areas", [])
            if topic_areas:
                lines.append(f"**Topic Areas**: {', '.join(topic_areas)}")
            task_types = patterns.get("typical_task_types", [])
            if task_types:
                lines.append(f"**Typical Tasks**: {', '.join(task_types)}")
            active_hours = patterns.get("active_hours", [])
            if active_hours:
                lines.append(f"**Active Hours**: {', '.join(map(str, active_hours))}")
            work_style = patterns.get("work_style")
            if work_style:
                lines.append(f"**Work Style**: {work_style}")
            lines.append("")

        indicators = profile.get("personality_indicators", {})
        if indicators:
            lines.append("**Personality Indicators (0-1 scale)**:")
            for key, val in indicators.items():
                lines.append(f"  - {key}: {val}")

        return "\n".join(lines)
