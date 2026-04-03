from typing import Dict, Any


class AgentBusinessLogic:
    def process_user_query(self, query: str, context: dict) -> Dict[str, Any]:
        return {
            "response": f"Echo: {query}",
            "thought_trace": [
                {"step": "perception", "content": f"Received query: {query}"},
                {"step": "reasoning", "content": "Processing..."}
            ],
            "tool_calls": [],
            "requires_confirmation": False
        }

    def save_chat_history(self, session_id: str, message: str, role: str, tool_calls=None) -> Dict[str, Any]:
        return {
            "session_id": session_id,
            "message": message,
            "role": role,
            "tool_calls": tool_calls
        }
