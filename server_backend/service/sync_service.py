from database.repositories import SyncRepository


class SyncService:
    def __init__(self):
        self.sync_repo = SyncRepository()

    def sync_from_client(self, user_id: int, data_type: str, data: list):
        """从客户端同步数据到服务器"""
        if data_type == 'schedules':
            synced_count = self.sync_repo.sync_schedules(user_id, data)
        elif data_type == 'tasks':
            synced_count = self.sync_repo.sync_tasks(user_id, data)
        elif data_type == 'chats':
            synced_count = self.sync_repo.sync_chats(user_id, data)
        else:
            return {'success': False, 'message': 'Invalid data type', 'synced_count': 0}
        
        return {
            'success': True,
            'message': f'Successfully synced {synced_count} {data_type}',
            'synced_count': synced_count
        }

    def sync_to_client(self, user_id: int, data_type: str):
        """从服务器同步数据到客户端"""
        data = self.sync_repo.get_synced_data(user_id, data_type)
        
        # 转换为可序列化的格式
        if data_type == 'schedules':
            serialized_data = [
                {
                    'id': item.id,
                    'title': item.title,
                    'description': item.description,
                    'start_time': item.start_time.isoformat(),
                    'end_time': item.end_time.isoformat(),
                    'location': item.location,
                    'event_type': item.event_type,
                    'source': item.source
                }
                for item in data
            ]
        elif data_type == 'tasks':
            serialized_data = [
                {
                    'id': item.id,
                    'title': item.title,
                    'description': item.description,
                    'due_date': item.due_date.isoformat() if item.due_date else None,
                    'priority': item.priority,
                    'status': item.status
                }
                for item in data
            ]
        elif data_type == 'chats':
            serialized_data = [
                {
                    'id': item.id,
                    'session_id': item.session_id,
                    'message': item.message,
                    'role': item.role,
                    'tool_calls': item.tool_calls,
                    'created_at': item.created_at.isoformat()
                }
                for item in data
            ]
        else:
            return {
                'success': False,
                'message': 'Invalid data type',
                'data': [],
                'synced_count': 0
            }
        
        return {
            'success': True,
            'message': f'Successfully synced {len(serialized_data)} {data_type}',
            'data': serialized_data,
            'synced_count': len(serialized_data)
        }
