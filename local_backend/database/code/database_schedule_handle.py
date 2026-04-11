from database.code.database_schedule_operations import ScheduleOperations


class ScheduleHandle:
    """日程功能调用入口"""

    def __init__(self):
        self.operations = ScheduleOperations()

    def create_schedule(self, user_id: str, title: str, start_time: str, end_time: str, **kwargs) -> dict:
        """创建日程入口"""
        # 验证输入
        if not user_id or not title or not start_time or not end_time:
            return {'ok': False, 'status': 400, 'message': 'user_id、title、start_time、end_time 不能为空'}
        
        try:
            schedule_id = self.operations.create_schedule(
                user_id=user_id,
                title=title,
                start_time=start_time,
                end_time=end_time,
                event_type=kwargs.get('event_type', 'personal'),
                location=kwargs.get('location'),
                description=kwargs.get('description'),
                related_link=kwargs.get('related_link'),
                recurrence_rule=kwargs.get('recurrence_rule'),
                color_tag=kwargs.get('color_tag'),
            )
            return {'ok': True, 'status': 201, 'data': {'schedule_id': schedule_id}}
        except Exception as e:
            return {'ok': False, 'status': 500, 'message': f'创建日程失败: {str(e)}'}

    def get_schedules(self, user_id: str) -> dict:
        """获取用户日程列表入口"""
        # 验证输入
        if not user_id:
            return {'ok': False, 'status': 400, 'message': 'user_id 不能为空'}
        
        try:
            schedules = self.operations.get_schedules_by_user(user_id)
            return {'ok': True, 'status': 200, 'data': schedules}
        except Exception as e:
            return {'ok': False, 'status': 500, 'message': f'获取日程失败: {str(e)}'}

    def update_schedule(self, user_id: str, schedule_id: int, **kwargs) -> dict:
        """更新日程入口"""
        # 验证输入
        if not schedule_id:
            return {'ok': False, 'status': 400, 'message': 'schedule_id 不能为空'}
        
        try:
            self.operations.update_schedule(
                user_id=user_id,
                schedule_id=schedule_id,
                title=kwargs.get('title'),
                start_time=kwargs.get('start_time'),
                end_time=kwargs.get('end_time'),
                location=kwargs.get('location'),
                description=kwargs.get('description'),
                related_link=kwargs.get('related_link'),
                recurrence_rule=kwargs.get('recurrence_rule'),
                color_tag=kwargs.get('color_tag'),
            )
            return {'ok': True, 'status': 200, 'message': '日程更新成功'}
        except ValueError as e:
            return {'ok': False, 'status': 404, 'message': str(e)}
        except Exception as e:
            return {'ok': False, 'status': 500, 'message': f'更新日程失败: {str(e)}'}

    def delete_schedule(self, user_id: str, schedule_id: int) -> dict:
        """删除日程入口"""
        # 验证输入
        if not schedule_id:
            return {'ok': False, 'status': 400, 'message': 'schedule_id 不能为空'}
        
        try:
            self.operations.delete_schedule(user_id, schedule_id)
            return {'ok': True, 'status': 200, 'message': '日程删除成功'}
        except ValueError as e:
            return {'ok': False, 'status': 404, 'message': str(e)}
        except Exception as e:
            return {'ok': False, 'status': 500, 'message': f'删除日程失败: {str(e)}'}