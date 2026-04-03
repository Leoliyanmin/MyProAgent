from typing import List, Dict, Any
from datetime import datetime


class ScheduleBusinessLogic:
    def check_schedule_conflict(self, schedules: List[Dict[str, Any]], new_schedule: Dict[str, Any]) -> bool:
        new_start = new_schedule.get('start_time')
        new_end = new_schedule.get('end_time')
        
        for schedule in schedules:
            if schedule.get('id') == new_schedule.get('id'):
                continue
            
            existing_start = schedule.get('start_time')
            existing_end = schedule.get('end_time')
            
            if (new_start < existing_end and new_end > existing_start):
                return True
        
        return False

    def optimize_schedule(self, schedules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return sorted(schedules, key=lambda x: x.get('start_time'))

    def get_weekly_schedule(self, schedules: List[Dict[str, Any]], week_start: datetime) -> List[Dict[str, Any]]:
        week_end = week_start + timedelta(days=7)
        return [s for s in schedules if week_start <= s.get('start_time') < week_end]
