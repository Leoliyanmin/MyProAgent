from database.code.database_command import (
    create_session,
    list_sessions_by_user,
    update_session_last_visited,
    delete_session,
    create_chat,
    list_chat_by_session,
    update_chat_trace,
    delete_chat,
    upsert_sync_state,
    get_sync_state,
)
from datetime import datetime


class ChatOperations:
    """聊天相关数据库操作封装"""

    @staticmethod
    def create_session(user_id: str) -> int:
        """创建会话"""
        now = datetime.utcnow().isoformat()
        session_id = create_session(
            user_id=user_id,
            session_title="",
            session_created_at=now,
            session_last_visited_at=now,
        )
        return session_id

    @staticmethod
    def get_sessions_by_user(user_id: str) -> list[dict]:
        """获取用户的所有会话"""
        return list_sessions_by_user(user_id)

    @staticmethod
    def update_session_last_visited(session_id: int) -> None:
        """更新会话最后访问时间"""
        now = datetime.utcnow().isoformat()
        update_session_last_visited(session_id=session_id, session_last_visited_at=now)

    @staticmethod
    def delete_session(session_id: int) -> None:
        """删除会话"""
        delete_session(session_id)

    @staticmethod
    def create_chat_message(
        session_id: int,
        role: str,
        message: str,
        thought_trace: str = None,
        tool_calls: str = None,
        tokens_usage: str = None,
    ) -> int:
        """创建聊天消息"""
        now = datetime.utcnow().isoformat()
        chat_id = create_chat(
            session_id=session_id,
            chat_role=role,
            chat_message_content=message,
            thought_trace=thought_trace,
            chat_tool_calls=tool_calls,
            chat_tokens_usage=tokens_usage,
            chat_created_at=now,
        )
        
        # 更新会话最后访问时间
        ChatOperations.update_session_last_visited(session_id)
        
        return chat_id

    @staticmethod
    def get_chat_history(session_id: int) -> list[dict]:
        """获取会话的聊天历史"""
        return list_chat_by_session(session_id)

    @staticmethod
    def update_chat_message(
        chat_id: int,
        thought_trace: str = None,
        tool_calls: str = None,
        tokens_usage: str = None,
    ) -> None:
        """更新聊天消息"""
        update_chat_trace(
            chat_id=chat_id,
            thought_trace=thought_trace,
            chat_tool_calls=tool_calls,
            chat_tokens_usage=tokens_usage,
        )

    @staticmethod
    def delete_chat_message(chat_id: int) -> None:
        """删除聊天消息"""
        delete_chat(chat_id)