from database.code.database_command import (
    create_data,
    list_data_by_user,
    get_data,
    update_data,
    delete_data,
    create_category,
    list_categories_by_user,
    upsert_sync_state,
    get_sync_state,
)
from datetime import datetime


class TaskOperations:
    """任务相关数据库操作封装"""

    @staticmethod
    def create_task(user_id: str, title: str, description: str = None, due_date: str = None) -> int:
        """创建任务"""
        # 确保任务分类存在
        task_category = TaskOperations._get_or_create_task_category(user_id)
        
        now = datetime.utcnow().isoformat()
        data_id = create_data(
            user_id=user_id,
            data_category_id=task_category['category_id'],
            data_content_type='task',
            data_title=title,
            data_content_text=description,
            data_link_url=None,
            data_release_time=None,
            data_ddl_time=due_date,
            data_is_previewable=0,
            data_created_at=now,
        )
        
        TaskOperations._update_sync_version(user_id)
        return data_id

    @staticmethod
    def get_tasks_by_user(user_id: str) -> list[dict]:
        """获取用户的所有任务"""
        # 获取任务分类ID
        categories = list_categories_by_user(user_id)
        task_category_ids = [cat['category_id'] for cat in categories if cat['category_kind'] == 'task']
        
        # 获取属于任务分类的数据
        all_data = list_data_by_user(user_id)
        return [d for d in all_data if d['data_category_id'] in task_category_ids]

    @staticmethod
    def update_task(user_id: str, task_id: int, title: str = None, description: str = None, due_date: str = None) -> None:
        """更新任务"""
        # 获取现有任务数据
        task_user_id = TaskOperations._get_task_user_id(task_id)
        if not task_user_id:
            raise ValueError(f"Task not found: {task_id}")
        
        # 验证用户权限
        if task_user_id != user_id:
            raise ValueError(f"Task not found: {task_id}")
        
        update_data(
            data_id=task_id,
            data_title=title,
            data_content_text=description,
            data_link_url=None,
            data_release_time=None,
            data_ddl_time=due_date,
            data_is_previewable=0,
        )
        
        TaskOperations._update_sync_version(user_id)

    @staticmethod
    def delete_task(user_id: str, task_id: int) -> None:
        """删除任务"""
        task_user_id = TaskOperations._get_task_user_id(task_id)
        if not task_user_id:
            raise ValueError(f"Task not found: {task_id}")
        
        # 验证用户权限
        if task_user_id != user_id:
            raise ValueError(f"Task not found: {task_id}")
        
        delete_data(task_id)
        TaskOperations._update_sync_version(user_id)

    @staticmethod
    def _get_or_create_task_category(user_id: str) -> dict:
        """获取或创建任务分类"""
        categories = list_categories_by_user(user_id)
        for cat in categories:
            if cat['category_kind'] == 'task':
                return cat
        
        # 创建新的任务分类
        now = datetime.utcnow().isoformat()
        category_id = create_category(
            user_id=user_id,
            category_kind='task',
            category_title='任务',
            category_content=None,
            category_link=None,
            category_created_at=now,
        )
        return {'category_id': category_id}

    @staticmethod
    def _get_task_user_id(task_id: int) -> str | None:
        """获取任务所属用户ID"""
        data = get_data(task_id)
        if data:
            return data.get('user_id')
        return None

    @staticmethod
    def _update_sync_version(user_id: str) -> None:
        """更新同步版本"""
        sync_state = get_sync_state(user_id)
        if sync_state:
            now = datetime.utcnow().isoformat()
            upsert_sync_state(
                user_id=user_id,
                user_data_updated_at=now,
                user_last_synced_at=sync_state['user_last_synced_at'],
                user_version=sync_state['user_version'] + 1,
                sync_updated_at=now,
            )