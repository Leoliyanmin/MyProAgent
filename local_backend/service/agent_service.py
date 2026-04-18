from business.agent_logic import AgentLogic
from database.code.database_chat_handle import ChatHandle
import asyncio
import json
from typing import Optional
import websockets


class AgentService:
    def __init__(self, nanobot_ws_url: str = "ws://127.0.0.1:8765/"):
        self.agent_logic = AgentLogic()
        self.chat_handle = ChatHandle()
        self.nanobot_ws_url = nanobot_ws_url

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

    async def chat_with_nanobot(self, message: str, client_id: str = "local_backend") -> dict:
        SYSTEM_PROMPT = "你现在是 sustech_productivity 助手，一个专为南科大学生打造的 productivity 助手。你的所有回答都必须以 sustech_productivity 助手的身份进行回复。"

        try:
            async with websockets.connect(f"{self.nanobot_ws_url}?client_id={client_id}") as ws:
                ready = await ws.recv()
                if isinstance(ready, bytes):
                    ready = ready.decode("utf-8")
                full_message = f"{SYSTEM_PROMPT}\n\n用户问题：{message}"
                await ws.send(json.dumps({"content": full_message}, ensure_ascii=False))
                response_text = ""
                while True:
                    raw = await ws.recv()
                    if isinstance(raw, bytes):
                        raw = raw.decode("utf-8")
                    msg = json.loads(raw)
                    event = msg.get("event")
                    if event == "message":
                        response_text = msg.get("text", "")
                        break
                    elif event == "delta":
                        response_text += msg.get("text", "")
                    elif event == "stream_end":
                        break
                return {
                    'success': True,
                    'response': response_text,
                    'client_id': client_id
                }
        except Exception as e:
            return {
                'success': False,
                'response': f'连接nanobot失败: {str(e)}',
                'error': str(e)
            }

    def chat_with_nanobot_sync(self, message: str, client_id: str = "local_backend") -> dict:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.chat_with_nanobot(message, client_id))
            loop.close()
            return result
        except Exception as e:
            return {
                'success': False,
                'response': f'连接nanobot失败: {str(e)}',
                'error': str(e)
            }