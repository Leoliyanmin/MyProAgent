from database.code.database_command import (
    create_schedule,
    list_schedule_by_user,
    get_schedule,
    update_schedule,
    delete_schedule,
    upsert_sync_state,
    get_sync_state,
)
from datetime import datetime


class ScheduleOperations:
    """日程相关数据库操作封装"""

    @staticmethod
    def create_schedule(
        user_id: str,
        title: str,
        start_time: str,
        end_time: str,
        event_type: str = 'personal',
        location: str = None,
        description: str = None,
        related_link: str = None,
        recurrence_rule: str = None,
        color_tag: str = None,
    ) -> int:
        """创建日程"""
        schedule_id = create_schedule(
            user_id=user_id,
            schedule_event_type=event_type,
            schedule_title=title,
            schedule_start_time=start_time,
            schedule_end_time=end_time,
            schedule_location=location,
            schedule_description=description,
            schedule_related_link=related_link,
            schedule_recurrence_rule=recurrence_rule,
            schedule_color_tag=color_tag,
        )
        
        ScheduleOperations._update_sync_version(user_id)
        return schedule_id

    @staticmethod
    def get_schedules_by_user(user_id: str) -> list[dict]:
        """获取用户的所有日程"""
        return list_schedule_by_user(user_id)

    @staticmethod
    def update_schedule(
        user_id: str,
        schedule_id: int,
        title: str = None,
        start_time: str = None,
        end_time: str = None,
        location: str = None,
        description: str = None,
        related_link: str = None,
        recurrence_rule: str = None,
        color_tag: str = None,
    ) -> None:
        """更新日程"""
        # 获取现有日程数据
        schedule_user_id = ScheduleOperations._get_schedule_user_id(schedule_id)
        if not schedule_user_id:
            raise ValueError(f"Schedule not found: {schedule_id}")
        
        # 验证用户权限
        if schedule_user_id != user_id:
            raise ValueError(f"Schedule not found: {schedule_id}")
        
        update_schedule(
            schedule_id=schedule_id,
            schedule_title=title,
            schedule_start_time=start_time,
            schedule_end_time=end_time,
            schedule_location=location,
            schedule_description=description,
            schedule_related_link=related_link,
            schedule_recurrence_rule=recurrence_rule,
            schedule_color_tag=color_tag,
        )
        
        ScheduleOperations._update_sync_version(user_id)

    @staticmethod
    def delete_schedule(user_id: str, schedule_id: int) -> None:
        """删除日程"""
        schedule_user_id = ScheduleOperations._get_schedule_user_id(schedule_id)
        if not schedule_user_id:
            raise ValueError(f"Schedule not found: {schedule_id}")
        
        # 验证用户权限
        if schedule_user_id != user_id:
            raise ValueError(f"Schedule not found: {schedule_id}")
        
        delete_schedule(schedule_id)
        ScheduleOperations._update_sync_version(user_id)

    @staticmethod
    def _get_schedule_user_id(schedule_id: int) -> str | None:
        """获取日程所属用户ID"""
        schedule = get_schedule(schedule_id)
        if schedule:
            return schedule.get('user_id')
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