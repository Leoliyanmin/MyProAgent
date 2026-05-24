import json
from local_backend.database.code.command.database_command import (
    create_interaction_log,
    list_interaction_logs_by_user,
    get_interaction_log,
    delete_interaction_log,
    count_interaction_logs_by_user,
)


class InteractionLogOperations:

    def log(self, interaction_data: dict) -> str:
        meta = interaction_data.get("metadata", {})
        user_input = interaction_data.get("user_input", {})
        agent_output = interaction_data.get("agent_output", {})
        tool_exec = interaction_data.get("tool_execution", {})

        conversation_id = meta.get("conversation_id", "")

        create_interaction_log(
            user_id=meta.get("user_id", ""),
            conversation_id=conversation_id,
            session_id=meta.get("session_id"),
            platform=meta.get("platform"),
            timestamp=meta.get("timestamp", ""),
            user_message=user_input.get("raw_message"),
            intent_category=user_input.get("intent_category"),
            keywords_json=json.dumps(user_input.get("keywords", []), ensure_ascii=False),
            language=user_input.get("language"),
            sentiment=user_input.get("sentiment"),
            urgency=user_input.get("urgency"),
            message_length=user_input.get("message_length"),
            contains_file_reference=str(user_input.get("contains_file_reference", "false")),
            agent_response=agent_output.get("raw_response"),
            agent_response_length=agent_output.get("response_length"),
            follow_up_required=1 if agent_output.get("follow_up_required") else 0,
            suggested_actions_json=json.dumps(agent_output.get("suggested_actions", []), ensure_ascii=False),
            tools_invoked_json=json.dumps(tool_exec.get("tools_invoked", []), ensure_ascii=False),
            files_accessed_json=json.dumps(tool_exec.get("files_accessed", []), ensure_ascii=False),
            total_execution_time_ms=tool_exec.get("total_execution_time_ms"),
        )
        return conversation_id

    def get(self, conversation_id: str) -> dict | None:
        row = get_interaction_log(conversation_id)
        if not row:
            return None
        return self._deserialize(row)

    def list_for_user(self, user_id: str, limit: int = 100) -> list:
        rows = list_interaction_logs_by_user(user_id, limit)
        return [self._deserialize(r) for r in rows]

    def delete(self, conversation_id: str) -> bool:
        existing = get_interaction_log(conversation_id)
        if not existing:
            return False
        delete_interaction_log(conversation_id)
        return True

    def count_for_user(self, user_id: str) -> int:
        return count_interaction_logs_by_user(user_id)

    def _deserialize(self, row: dict) -> dict:
        return {
            "metadata": {
                "user_id": row.get("user_id"),
                "session_id": row.get("session_id"),
                "platform": row.get("platform"),
                "conversation_id": row.get("conversation_id"),
                "timestamp": row.get("timestamp"),
            },
            "user_input": {
                "raw_message": row.get("user_message"),
                "intent_category": row.get("intent_category"),
                "keywords": json.loads(row["keywords_json"]) if row.get("keywords_json") else [],
                "language": row.get("language"),
                "sentiment": row.get("sentiment"),
                "urgency": row.get("urgency"),
                "message_length": row.get("message_length"),
                "contains_file_reference": row.get("contains_file_reference", "false"),
            },
            "agent_output": {
                "raw_response": row.get("agent_response"),
                "response_length": row.get("agent_response_length"),
                "follow_up_required": bool(row.get("follow_up_required")),
                "suggested_actions": json.loads(row["suggested_actions_json"]) if row.get("suggested_actions_json") else [],
            },
            "tool_execution": {
                "tools_invoked": json.loads(row["tools_invoked_json"]) if row.get("tools_invoked_json") else [],
                "files_accessed": json.loads(row["files_accessed_json"]) if row.get("files_accessed_json") else [],
                "total_execution_time_ms": row.get("total_execution_time_ms"),
            },
        }
