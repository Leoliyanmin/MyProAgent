from database.repositories import AgentChatRepository
from business.agent_logic import AgentLogic


class AgentService:
    def __init__(self):
        self.agent_logic = AgentLogic()
        self.chat_repo = AgentChatRepository()

    def process_query(self, user_id: int, message: str, session_id: str):
        # 处理用户查询
        result = self.agent_logic.process_query(user_id, message, session_id)
        
        # 保存用户消息
        user_chat_data = {
            'user_id': user_id,
            'session_id': session_id,
            'message': message,
            'role': 'user'
        }
        self.chat_repo.create_chat_message(user_chat_data)
        
        # 保存助手回复
        assistant_chat_data = {
            'user_id': user_id,
            'session_id': session_id,
            'message': result['response'],
            'role': 'assistant',
            'tool_calls': str(result.get('tool_calls', []))
        }
        self.chat_repo.create_chat_message(assistant_chat_data)
        
        return result

    def get_chat_history(self, session_id: str):
        chats = self.chat_repo.get_chat_history_by_session(session_id)
        return [
            {
                'id': chat.id,
                'message': chat.message,
                'role': chat.role,
                'tool_calls': chat.tool_calls,
                'created_at': chat.created_at.isoformat()
            }
            for chat in chats
        ]
