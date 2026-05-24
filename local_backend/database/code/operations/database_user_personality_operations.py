import json
from local_backend.database.code.command.database_command import (
    upsert_user_personality,
    get_user_personality,
    delete_user_personality,
)


class UserPersonalityOperations:

    def upsert_profile(self, user_id: str, profile_data: dict) -> None:
        mbti = profile_data.get("mbti_inference", {})
        kwargs = {}
        if "interests_identified" in profile_data:
            kwargs["interests_json"] = json.dumps(profile_data["interests_identified"], ensure_ascii=False)
        if "skills_demonstrated" in profile_data:
            kwargs["skills_json"] = json.dumps(profile_data["skills_demonstrated"], ensure_ascii=False)
        if "preferences_inferred" in profile_data:
            kwargs["preferences_json"] = json.dumps(profile_data["preferences_inferred"], ensure_ascii=False)
        if "study_work_patterns" in profile_data:
            kwargs["study_work_patterns_json"] = json.dumps(profile_data["study_work_patterns"], ensure_ascii=False)
        if "personality_indicators" in profile_data:
            kwargs["personality_indicators_json"] = json.dumps(profile_data["personality_indicators"], ensure_ascii=False)
        if mbti.get("mbti_type") is not None:
            kwargs["mbti_type"] = mbti["mbti_type"]
        if "scores" in mbti:
            kwargs["mbti_scores_json"] = json.dumps(mbti["scores"], ensure_ascii=False)
        if "confidence" in mbti:
            kwargs["mbti_confidence"] = mbti["confidence"]
        if "description" in mbti:
            kwargs["mbti_description"] = mbti["description"]
        if "last_updated" in mbti:
            kwargs["mbti_last_updated"] = mbti["last_updated"]
        if "interaction_count" in profile_data:
            kwargs["interaction_count"] = profile_data["interaction_count"]
        if kwargs:
            upsert_user_personality(user_id=user_id, **kwargs)

    def get_profile(self, user_id: str) -> dict | None:
        row = get_user_personality(user_id)
        if not row:
            return None
        return {
            "user_id": row["user_id"],
            "interests_identified": json.loads(row["interests_json"]) if row.get("interests_json") else [],
            "skills_demonstrated": json.loads(row["skills_json"]) if row.get("skills_json") else [],
            "preferences_inferred": json.loads(row["preferences_json"]) if row.get("preferences_json") else {},
            "study_work_patterns": json.loads(row["study_work_patterns_json"]) if row.get("study_work_patterns_json") else {},
            "personality_indicators": json.loads(row["personality_indicators_json"]) if row.get("personality_indicators_json") else {},
            "mbti_inference": {
                "mbti_type": row.get("mbti_type"),
                "scores": json.loads(row["mbti_scores_json"]) if row.get("mbti_scores_json") else {},
                "confidence": row.get("mbti_confidence", 0.0),
                "description": row.get("mbti_description", ""),
                "last_updated": row.get("mbti_last_updated"),
            },
            "interaction_count": row.get("interaction_count", 0),
            "last_updated": row.get("last_updated"),
        }

    def update_mbti(self, user_id: str, mbti_result: dict) -> None:
        import datetime
        upsert_user_personality(
            user_id=user_id,
            mbti_type=mbti_result.get("mbti_type"),
            mbti_scores_json=json.dumps(mbti_result.get("scores", {}), ensure_ascii=False),
            mbti_confidence=mbti_result.get("confidence", 0.0),
            mbti_description=mbti_result.get("description", ""),
            mbti_last_updated=datetime.datetime.utcnow().isoformat(),
        )

    def delete_profile(self, user_id: str) -> bool:
        existing = get_user_personality(user_id)
        if not existing:
            return False
        delete_user_personality(user_id)
        return True
