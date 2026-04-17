from database.code.database_chat_operations import ChatOperations


class ChatHandle:
    """聊天功能调用入口"""

    def __init__(self):
        self.operations = ChatOperations()

    def create_session(self, user_id: str) -> dict:
        """创建会话入口"""
        # 验证输入
        if not user_id:
            return {'ok': False, 'status': 400, 'message': 'user_id 不能为空'}
        
        try:
            session_id = self.operations.create_session(user_id)
            return {'ok': True, 'status': 201, 'data': {'session_id': session_id}}
        except Exception as e:
            return {'ok': False, 'status': 500, 'message': f'创建会话失败: {str(e)}'}

    def get_sessions(self, user_id: str) -> dict:
        """获取用户会话列表入口"""
        # 验证输入
        if not user_id:
            return {'ok': False, 'status': 400, 'message': 'user_id 不能为空'}
        
        try:
            sessions = self.operations.get_sessions_by_user(user_id)
            return {'ok': True, 'status': 200, 'data': sessions}
        except Exception as e:
            return {'ok': False, 'status': 500, 'message': f'获取会话失败: {str(e)}'}

    def create_chat_message(self, session_id: int, role: str, message: str, **kwargs) -> dict:
        """创建聊天消息入口"""
        # 验证输入
        if not session_id or not role or not message:
            return {'ok': False, 'status': 400, 'message': 'session_id、role、message 不能为空'}
        
        # 验证角色
        if role not in ['user', 'assistant']:
            return {'ok': False, 'status': 400, 'message': 'role 必须是 user 或 assistant'}
        
        try:
            chat_id = self.operations.create_chat_message(
                session_id=session_id,
                role=role,
                message=message,
                thought_trace=kwargs.get('thought_trace'),
                tool_calls=kwargs.get('tool_calls'),
                tokens_usage=kwargs.get('tokens_usage'),
            )
            return {'ok': True, 'status': 201, 'data': {'chat_id': chat_id}}
        except Exception as e:
            return {'ok': False, 'status': 500, 'message': f'创建消息失败: {str(e)}'}

    def get_chat_history(self, session_id: int) -> dict:
        """获取会话聊天历史入口"""
        # 验证输入
        if not session_id:
            return {'ok': False, 'status': 400, 'message': 'session_id 不能为空'}
        
        try:
            history = self.operations.get_chat_history(session_id)
            return {'ok': True, 'status': 200, 'data': history}
        except Exception as e:
            return {'ok': False, 'status': 500, 'message': f'获取聊天历史失败: {str(e)}'}

    def delete_session(self, session_id: int) -> dict:
        """删除会话入口"""
        # 验证输入
        if not session_id:
            return {'ok': False, 'status': 400, 'message': 'session_id 不能为空'}
        
        try:
            self.operations.delete_session(session_id)
            return {'ok': True, 'status': 200, 'message': '会话删除成功'}
        except Exception as e:
            return {'ok': False, 'status': 500, 'message': f'删除会话失败: {str(e)}'}