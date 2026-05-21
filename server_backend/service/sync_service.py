import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.code.handle.database_synchronize_handle import ServerSyncHandle
from database.code.command import database_command as db
from logging_config import get_logger

# 创建日志器
logger = get_logger("sync_service")


class SyncService:
    def __init__(self):
        self.sync_handle = ServerSyncHandle()
        logger.info("SyncService 初始化完成")

    def sync_from_client(self, user_id: str, data_type: str, sync_data: list):
        """从客户端同步数据到服务器"""
        logger.info(f"开始从客户端同步数据: user_id={user_id}, data_type={data_type}")

        user = db.get_user(user_id)
        if not user:
            return {"success": False, "message": "User not found"}

        if data_type == "task":
            db.delete_server_tasks_by_user(user_id)
            for row in sync_data:
                if not isinstance(row, dict):
                    continue
                db.create_server_task(
                    user_id=user_id,
                    title=row.get("title", ""),
                    description=row.get("description"),
                    priority=row.get("priority", 2),
                    status=row.get("status", "pending"),
                    due_date=row.get("due_date"),
                    created_at=row.get("created_at"),
                )
            return {"success": True, "message": "Synced", "synced_count": len(sync_data)}

        if data_type == "user_setting":
            if isinstance(sync_data, list) and sync_data:
                db.upsert_user_setting(user_id, **sync_data[0])
            elif isinstance(sync_data, dict):
                db.upsert_user_setting(user_id, **sync_data)
            return {"success": True, "message": "Synced", "synced_count": 1}

        push_payload = {
            "user": {
                "user_id": user_id,
                "user_version": 1,
                "user_data_updated_at": "2026-01-01T00:00:00+00:00",
            },
            data_type: sync_data if isinstance(sync_data, list) else [sync_data],
        }

        try:
            result = self.sync_handle.handle_push(push_payload)
            if not result.get("ok"):
                logger.error(f"从客户端同步数据失败: {result.get('message', 'Sync failed')}, user_id={user_id}")
                return {"success": False, "message": result.get("message", "Sync failed")}

            synced_count = len(sync_data) if isinstance(sync_data, list) else 1
            logger.info(f"从客户端同步数据成功: user_id={user_id}, data_type={data_type}, synced_count={synced_count}")

            return {
                "success": True,
                "message": "Sync successful",
                "synced_count": synced_count,
            }
        except Exception as e:
            logger.error(f"从客户端同步数据发生异常: {str(e)}, user_id={user_id}", exc_info=True)
            return {"success": False, "message": f"Sync error: {str(e)}"}

    def sync_to_client(self, user_id: str, data_type: str):
        """从服务器同步数据到客户端"""
        logger.info(f"开始向客户端同步数据: user_id={user_id}, data_type={data_type}")
        
        try:
            result = self.sync_handle.handle_pull(user_id)
            if not result.get('ok'):
                logger.error(f"向客户端同步数据失败: {result.get('message', 'Sync failed')}, user_id={user_id}")
                return {'success': False, 'message': result.get('message', 'Sync failed')}
            
            packet = result.get('packet', {})
            data = packet.get(data_type, [])
            logger.info(f"向客户端同步数据成功: user_id={user_id}, data_type={data_type}, synced_count={len(data)}")
            
            return {
                'success': True,
                'message': 'Sync successful',
                'data': data,
                'synced_count': len(data)
            }
        except Exception as e:
            logger.error(f"向客户端同步数据发生异常: {str(e)}, user_id={user_id}", exc_info=True)
            return {'success': False, 'message': f'Sync error: {str(e)}'}

    def handle_probe(self, user_id: str, client_version: int):
        """处理同步探测"""
        logger.debug(f"处理同步探测: user_id={user_id}, client_version={client_version}")
        
        result = self.sync_handle.handle_probe({
            'user_id': user_id,
            'client_user_version': client_version
        })
        
        if result.get('ok'):
            logger.debug(f"同步探测成功: user_id={user_id}, server_version={result.get('server_user_version')}")
        else:
            logger.warning(f"同步探测失败: {result.get('message')}, user_id={user_id}")
        
        return result
