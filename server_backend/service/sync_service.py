from database.code.database_synchronize_handle import ServerSyncHandle


class SyncService:
    def __init__(self):
        self.sync_handle = ServerSyncHandle()

    def sync_from_client(self, user_id: str, data_type: str, sync_data: dict):
        """从客户端同步数据到服务器"""
        # 构建完整的 push payload
        push_payload = {
            "user": {
                "user_id": user_id,
                "user_version": 1,
                "user_data_updated_at": "2026-01-01T00:00:00+00:00",
            },
            data_type: sync_data if isinstance(sync_data, list) else [sync_data],
        }
        result = self.sync_handle.handle_push(push_payload)
        if not result.get('ok'):
            return {'success': False, 'message': result.get('message', 'Sync failed')}
        
        return {
            'success': True,
            'message': 'Sync successful',
            'synced_count': len(sync_data) if isinstance(sync_data, list) else 1
        }

    def sync_to_client(self, user_id: str, data_type: str):
        """从服务器同步数据到客户端"""
        result = self.sync_handle.handle_pull(user_id)
        if not result.get('ok'):
            return {'success': False, 'message': result.get('message', 'Sync failed')}
        
        packet = result.get('packet', {})
        data = packet.get(data_type, [])
        return {
            'success': True,
            'message': 'Sync successful',
            'data': data,
            'synced_count': len(data)
        }

    def handle_probe(self, user_id: str, client_version: int):
        """处理同步探测"""
        result = self.sync_handle.handle_probe({
            'user_id': user_id,
            'client_user_version': client_version
        })
        return result
