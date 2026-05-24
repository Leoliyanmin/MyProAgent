import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from local_backend.database.code.command.database_command import (
    upsert_user_personality, create_interaction_log, create_api_key,
    get_user_personality, get_interaction_log, list_api_keys_by_user,
)


def migrate_profiles() -> int:
    profile_dir = Path(__file__).resolve().parent.parent.parent.parent / "personality" / "profiles"
    if not profile_dir.exists():
        print(f"  [skip] profile dir not found: {profile_dir}")
        return 0
    imported = 0
    for json_file in profile_dir.glob("*.json"):
        user_id = json_file.stem
        existing = get_user_personality(user_id)
        if existing:
            print(f"  [skip] profile already in DB: {user_id}")
            continue
        with open(json_file, "r", encoding="utf-8") as f:
            profile = json.load(f)
        mbti = profile.get("mbti_inference", {})
        upsert_user_personality(
            user_id=user_id,
            interests_json=json.dumps(profile.get("interests_identified", []), ensure_ascii=False),
            skills_json=json.dumps(profile.get("skills_demonstrated", []), ensure_ascii=False),
            preferences_json=json.dumps(profile.get("preferences_inferred", {}), ensure_ascii=False),
            study_work_patterns_json=json.dumps(profile.get("study_work_patterns", {}), ensure_ascii=False),
            personality_indicators_json=json.dumps(profile.get("personality_indicators", {}), ensure_ascii=False),
            mbti_type=mbti.get("mbti_type"),
            mbti_scores_json=json.dumps(mbti.get("scores", {}), ensure_ascii=False),
            mbti_confidence=mbti.get("confidence", 0.0),
            mbti_description=mbti.get("description", ""),
            interaction_count=profile.get("interaction_count", 0),
            mbti_last_updated=mbti.get("last_updated"),
        )
        imported += 1
        print(f"  [ok] imported profile: {user_id}")
    return imported


def migrate_interactions() -> int:
    interaction_dir = Path(__file__).resolve().parent.parent.parent.parent / "personality" / "interactions"
    if not interaction_dir.exists():
        print(f"  [skip] interaction dir not found: {interaction_dir}")
        return 0
    imported = 0
    for json_file in interaction_dir.glob("*.json"):
        conv_id = json_file.stem
        existing = get_interaction_log(conv_id)
        if existing:
            continue
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        meta = data.get("metadata", {})
        ui = data.get("user_input", {})
        ao = data.get("agent_output", {})
        te = data.get("tool_execution", {})

        create_interaction_log(
            user_id=meta.get("user_id", ""),
            conversation_id=meta.get("conversation_id", conv_id),
            session_id=meta.get("session_id"),
            platform=meta.get("platform"),
            timestamp=meta.get("timestamp", ""),
            user_message=ui.get("raw_message"),
            intent_category=ui.get("intent_category"),
            keywords_json=json.dumps(ui.get("keywords", []), ensure_ascii=False),
            language=ui.get("language"),
            sentiment=ui.get("sentiment"),
            urgency=ui.get("urgency"),
            message_length=ui.get("message_length"),
            contains_file_reference=str(ui.get("contains_file_reference", "false")),
            agent_response=ao.get("raw_response"),
            agent_response_length=ao.get("response_length"),
            follow_up_required=1 if ao.get("follow_up_required") else 0,
            suggested_actions_json=json.dumps(ao.get("suggested_actions", []), ensure_ascii=False),
            tools_invoked_json=json.dumps(te.get("tools_invoked", []), ensure_ascii=False),
            files_accessed_json=json.dumps(te.get("files_accessed", []), ensure_ascii=False),
            total_execution_time_ms=te.get("total_execution_time_ms"),
        )
        imported += 1
    if imported:
        print(f"  [ok] imported {imported} interactions")
    return imported


def migrate_api_keys() -> int:
    key_file = Path(__file__).resolve().parent.parent / "data" / "api_keys.jsonl"
    if not key_file.exists():
        print(f"  [skip] api_keys.jsonl not found: {key_file}")
        return 0
    imported = 0
    with open(key_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            key_id = entry.get("key_id", "")
            existing = list_api_keys_by_user(entry.get("user_id", ""))
            if any(e.get("key_id") == key_id for e in existing):
                continue
            create_api_key(
                user_id=entry.get("user_id", ""),
                key_id=key_id,
                provider=entry.get("provider", ""),
                api_key_plain=entry.get("api_key", ""),
                api_base=entry.get("api_base", ""),
                model=entry.get("model", ""),
            )
            imported += 1
    if imported:
        print(f"  [ok] imported {imported} API keys")
    return imported


if __name__ == "__main__":
    print("=== Migrating personality data to DB ===")
    profiles = migrate_profiles()
    interactions = migrate_interactions()
    apikeys = migrate_api_keys()
    print(f"\nDone: {profiles} profiles, {interactions} interactions, {apikeys} API keys")
