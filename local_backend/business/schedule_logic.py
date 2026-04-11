from datetime import datetime


class ScheduleLogic:
    def validate_schedule(self, schedule_data: dict) -> dict:
        """验证日程数据"""
        if not schedule_data.get('title'):
            return {'success': False, 'message': 'Title is required'}
        
        if not schedule_data.get('start_time') or not schedule_data.get('end_time'):
            return {'success': False, 'message': 'Start and end times are required'}
        
        try:
            # 检查是否已经是datetime对象
            start_time = schedule_data['start_time']
            end_time = schedule_data['end_time']
            
            # 如果是字符串，转换为datetime对象
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time)
            if isinstance(end_time, str):
                end_time = datetime.fromisoformat(end_time)
            
            if start_time >= end_time:
                return {'success': False, 'message': 'Start time must be before end time'}
        except ValueError:
            return {'success': False, 'message': 'Invalid date format'}
        
        return {'success': True}

    def check_conflicts(self, existing_schedules: list, new_schedule: dict) -> bool:
        """检查日程冲突"""
        # 检查是否已经是datetime对象
        new_start = new_schedule['start_time']
        new_end = new_schedule['end_time']
        
        # 如果是字符串，转换为datetime对象
        if isinstance(new_start, str):
            new_start = datetime.fromisoformat(new_start)
        if isinstance(new_end, str):
            new_end = datetime.fromisoformat(new_end)
        
        for schedule in existing_schedules:
            existing_start = schedule.start_time
            existing_end = schedule.end_time
            
            if (new_start < existing_end) and (new_end > existing_start):
                return True
        
        return False
