from business.schedule_logic import ScheduleLogic
from database.code.handle.database_schedule_handle import ScheduleHandle


class ScheduleService:
    def __init__(self):
        self.schedule_logic = ScheduleLogic()
        self.schedule_handle = ScheduleHandle()

    def create_schedule(self, user_id: str, schedule_data: dict):
        title = schedule_data.get('title', '')
        start_time = schedule_data.get('start_time', '')
        end_time = schedule_data.get('end_time', '')
        
        if not title or not start_time or not end_time:
            return {'success': False, 'message': '标题、开始时间和结束时间不能为空'}
        
        result = self.schedule_handle.create_schedule(
            user_id,
            title,
            start_time,
            end_time,
            event_type=schedule_data.get('event_type', 'personal'),
            priority=schedule_data.get('priority'),
            location=schedule_data.get('location'),
            description=schedule_data.get('description'),
            related_link=schedule_data.get('related_link'),
            recurrence_rule=schedule_data.get('recurrence_rule'),
            color_tag=schedule_data.get('color_tag'),
        )
        if not result['ok']:
            return {'success': False, 'message': result['message']}
        
        return {
            'success': True,
            'schedule_id': result['data']['schedule_id']
        }

    def get_schedules(self, user_id: str):
        result = self.schedule_handle.get_schedules(user_id)
        if not result['ok']:
            return {'success': False, 'message': result['message']}
        
        return {
            'success': True,
            'schedules': result['data']
        }

    def update_schedule(self, user_id: str, schedule_id: int, schedule_data: dict):
        result = self.schedule_handle.update_schedule(
            user_id,
            schedule_id,
            title=schedule_data.get('title'),
            start_time=schedule_data.get('start_time'),
            end_time=schedule_data.get('end_time'),
            priority=schedule_data.get('priority'),
            location=schedule_data.get('location'),
            description=schedule_data.get('description'),
            related_link=schedule_data.get('related_link'),
            recurrence_rule=schedule_data.get('recurrence_rule'),
            color_tag=schedule_data.get('color_tag'),
        )
        if not result['ok']:
            return {'success': False, 'message': result['message']}
        
        return {'success': True, 'message': '日程更新成功'}

    def delete_schedule(self, user_id: str, schedule_id: int):
        result = self.schedule_handle.delete_schedule(user_id, schedule_id)
        if not result['ok']:
            return {'success': False, 'message': result['message']}
        
        return {'success': True, 'message': '日程删除成功'}