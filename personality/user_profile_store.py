import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


class UserProfileStore:
    def __init__(self, profile_dir: Optional[Path] = None):
        if profile_dir is None:
            profile_dir = Path(__file__).parent / "profiles"
        self.profile_dir = profile_dir
        self.profile_dir.mkdir(parents=True, exist_ok=True)

    def update_profile(self, user_id: str, profile_update: Dict[str, Any]) -> None:
        profile_file = self.profile_dir / f"{user_id}.json"

        if profile_file.exists():
            with open(profile_file, "r", encoding="utf-8") as f:
                profile = json.load(f)
        else:
            profile = self._create_default_profile(user_id)

        self._merge_profile_update(profile, profile_update)
        profile["last_updated"] = datetime.now().isoformat()

        with open(profile_file, "w", encoding="utf-8") as f:
            json.dump(profile, f, ensure_ascii=False, indent=2)

    def get_profile(self, user_id: str) -> Dict[str, Any]:
        profile_file = self.profile_dir / f"{user_id}.json"
        if profile_file.exists():
            with open(profile_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return self._create_default_profile(user_id)

    def _create_default_profile(self, user_id: str) -> Dict[str, Any]:
        return {
            "user_id": user_id,
            "interests_identified": [],
            "skills_demonstrated": [],
            "preferences_inferred": {
                "communication_style": "casual",
                "response_length_preference": "medium",
                "preferred_language": "zh",
                "preferred_tool_usage": "automatic"
            },
            "study_work_patterns": {
                "topic_areas": [],
                "typical_task_types": [],
                "active_hours": [],
                "work_style": "flexible"
            },
            "personality_indicators": {
                "detail_oriented": 0.5,
                "proactive": 0.5,
                "collaborative": 0.5
            },
            "mbti_inference": {
                "mbti_type": None,
                "scores": {},
                "confidence": 0.0,
                "last_updated": None
            },
            "interaction_count": 0,
            "last_updated": None
        }

    def _merge_profile_update(self, profile: Dict[str, Any], update: Dict[str, Any]) -> None:
        profile["interaction_count"] += 1

        if "interests_identified" in update:
            existing_interests = {i["topic"] for i in profile.get("interests_identified", [])}
            for interest in update["interests_identified"]:
                if interest["topic"] not in existing_interests:
                    profile.setdefault("interests_identified", []).append(interest)

        if "skills_demonstrated" in update:
            existing_skills = {s["skill"] for s in profile.get("skills_demonstrated", [])}
            for skill in update["skills_demonstrated"]:
                if skill["skill"] not in existing_skills:
                    profile.setdefault("skills_demonstrated", []).append(skill)

        if "preferences_inferred" in update:
            profile.setdefault("preferences_inferred", {}).update(update["preferences_inferred"])

        if "study_work_patterns" in update:
            current_patterns = profile.get("study_work_patterns", {})
            new_patterns = update["study_work_patterns"]
            for key in ["topic_areas", "typical_task_types", "active_hours"]:
                if key in new_patterns:
                    existing = set(current_patterns.get(key, []))
                    new_items = set(new_patterns[key])
                    current_patterns[key] = list(existing | new_items)
            if "work_style" in new_patterns:
                current_patterns["work_style"] = new_patterns["work_style"]

        if "personality_indicators" in update:
            current = profile.get("personality_indicators", {})
            new = update["personality_indicators"]
            for key, value in new.items():
                if key in current:
                    current[key] = (current[key] + value) / 2
                else:
                    current[key] = value

    def update_mbti(self, user_id: str, mbti_result: Dict[str, Any]) -> None:
        profile = self.get_profile(user_id)
        profile["mbti_inference"] = {
            "mbti_type": mbti_result.get("mbti_type"),
            "scores": mbti_result.get("scores", {}),
            "confidence": mbti_result.get("confidence", 0.0),
            "description": mbti_result.get("description", ""),
            "last_updated": datetime.now().isoformat()
        }
        profile["last_updated"] = datetime.now().isoformat()

        with open(self.profile_dir / f"{user_id}.json", "w", encoding="utf-8") as f:
            json.dump(profile, f, ensure_ascii=False, indent=2)

    def delete_profile(self, user_id: str) -> bool:
        profile_file = self.profile_dir / f"{user_id}.json"
        if profile_file.exists():
            profile_file.unlink()
            return True
        return False
