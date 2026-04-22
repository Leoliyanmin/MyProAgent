from business.agent_logic import AgentLogic
from database.code.handle.database_chat_handle import ChatHandle


class AgentService:
    def __init__(self):
        self.agent_logic = AgentLogic()
        self.chat_handle = ChatHandle()

    def process_query(self, user_id: str, message: str, session_id: str = None):
        # 如果没有 session_id，创建一个新会话
        if not session_id:
            session_result = self.chat_handle.create_session(user_id)
            if not session_result['ok']:
                return {'response': '创建会话失败', 'thought_trace': [], 'tool_calls': []}
            session_id = session_result['data']['session_id']
        
        # 创建用户消息
        user_msg_result = self.chat_handle.create_chat_message(session_id, 'user', message)
        if not user_msg_result['ok']:
            print(f"Failed to create user message: {user_msg_result['message']}")
        
        # 处理查询
        result = self.agent_logic.process_query(user_id, message, str(session_id))
        
        # 创建助手消息
        assistant_msg_result = self.chat_handle.create_chat_message(
            session_id,
            'assistant',
            result['response'],
            thought_trace=str(result.get('thought_trace', [])),
            tool_calls=str(result.get('tool_calls', [])),
        )
        if not assistant_msg_result['ok']:
            print(f"Failed to create assistant message: {assistant_msg_result['message']}")
        
        return result

    def get_chat_history(self, user_id: str, session_id: str):
        try:
            session_id_int = int(session_id)
        except ValueError:
            return {'success': False, 'message': 'Invalid session ID'}
        
        result = self.chat_handle.get_chat_history(session_id_int)
        if not result['ok']:
            return {'success': False, 'message': result['message']}
        
        return {
            'success': True,
            'history': result['data']
        }