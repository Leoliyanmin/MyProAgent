from database.repositories import ScheduleRepository
from business.schedule_logic import ScheduleLogic


class ScheduleService:
    def __init__(self):
        self.schedule_repo = ScheduleRepository()
        self.schedule_logic = ScheduleLogic()

    def create_schedule(self, user_id: int, schedule_data: dict):
        validation = self.schedule_logic.validate_schedule(schedule_data)
        if not validation['success']:
            return validation
        
        existing_schedules = self.schedule_repo.get_schedules_by_user(user_id)
        if self.schedule_logic.check_conflicts(existing_schedules, schedule_data):
            return {'success': False, 'message': 'Schedule conflict detected'}
        
        schedule_data['user_id'] = user_id
        schedule = self.schedule_repo.create_schedule(schedule_data)
        
        return {
            'success': True,
            'schedule': {
                'id': schedule.id,
                'title': schedule.title,
                'description': schedule.description,
                'start_time': schedule.start_time.isoformat(),
                'end_time': schedule.end_time.isoformat(),
                'location': schedule.location,
                'event_type': schedule.event_type,
                'source': schedule.source
            }
        }

    def get_user_schedules(self, user_id: int):
        schedules = self.schedule_repo.get_schedules_by_user(user_id)
        return [
            {
                'id': s.id,
                'title': s.title,
                'description': s.description,
                'start_time': s.start_time.isoformat(),
                'end_time': s.end_time.isoformat(),
                'location': s.location,
                'event_type': s.event_type,
                'source': s.source
            }
            for s in schedules
        ]

    def update_schedule(self, schedule_id: int, update_data: dict):
        schedule = self.schedule_repo.get_schedule_by_id(schedule_id)
        if not schedule:
            return {'success': False, 'message': 'Schedule not found'}
        
        if 'start_time' in update_data or 'end_time' in update_data:
            temp_data = {'start_time': schedule.start_time.isoformat(), 'end_time': schedule.end_time.isoformat()}
            temp_data.update(update_data)
            validation = self.schedule_logic.validate_schedule(temp_data)
            if not validation['success']:
                return validation
        
        schedule = self.schedule_repo.update_schedule(schedule_id, update_data)
        if schedule:
            return {'success': True, 'message': 'Schedule updated successfully'}
        return {'success': False, 'message': 'Schedule not found'}

    def delete_schedule(self, schedule_id: int):
        if self.schedule_repo.delete_schedule(schedule_id):
            return {'success': True, 'message': 'Schedule deleted successfully'}
        return {'success': False, 'message': 'Schedule not found'}
