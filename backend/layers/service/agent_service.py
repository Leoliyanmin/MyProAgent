from layers.database.repositories import AgentChatRepository
from layers.business.agent_logic import AgentBusinessLogic
import uuid


class AgentService:
    def __init__(self):
        self.chat_repo = AgentChatRepository()
        self.agent_logic = AgentBusinessLogic()

    def process_query(self, user_id: int, query: str, session_id: str = None):
        if not session_id:
            session_id = str(uuid.uuid4())
        
        context = {
            'user_id': user_id,
            'session_id': session_id
        }
        
        result = self.agent_logic.process_user_query(query, context)
        
        self.chat_repo.create_chat({
            'user_id': user_id,
            'session_id': session_id,
            'message': query,
            'role': 'user',
            'tool_calls': None
        })
        
        self.chat_repo.create_chat({
            'user_id': user_id,
            'session_id': session_id,
            'message': result['response'],
            'role': 'assistant',
            'tool_calls': str(result.get('tool_calls', []))
        })
        
        return {
            'session_id': session_id,
            'response': result['response'],
            'thought_trace': result['thought_trace'],
            'tool_calls': result.get('tool_calls', []),
            'requires_confirmation': result.get('requires_confirmation', False)
        }

    def get_chat_history(self, session_id: str):
        chats = self.chat_repo.get_chats_by_session(session_id)
        return [
            {
                'id': c.id,
                'message': c.message,
                'role': c.role,
                'tool_calls': c.tool_calls,
                'created_at': c.created_at.isoformat()
            }
            for c in chats
        ]
