from datetime import datetime
import pytest
from business.schedule_logic import ScheduleLogic


class FakeSchedule:
    def __init__(self, start_time, end_time):
        self.start_time = start_time
        self.end_time = end_time


class TestScheduleValidate:
    def setup_method(self):
        self.logic = ScheduleLogic()

    def test_rejects_missing_title(self):
        result = self.logic.validate_schedule({})
        assert result['success'] is False
        assert 'Title' in result['message']

    def test_rejects_missing_start_time(self):
        result = self.logic.validate_schedule({'title': 'Meeting', 'end_time': datetime(2026, 5, 20, 11)})
        assert result['success'] is False
        assert 'Start' in result['message']

    def test_rejects_missing_end_time(self):
        result = self.logic.validate_schedule({'title': 'Meeting', 'start_time': datetime(2026, 5, 20, 10)})
        assert result['success'] is False
        assert 'end' in result['message'].lower()

    def test_rejects_start_after_end(self):
        result = self.logic.validate_schedule({
            'title': 'Meeting',
            'start_time': datetime(2026, 5, 20, 12),
            'end_time': datetime(2026, 5, 20, 10),
        })
        assert result['success'] is False
        assert 'start' in result['message'].lower()

    def test_accepts_valid_schedule(self):
        result = self.logic.validate_schedule({
            'title': 'Meeting',
            'start_time': datetime(2026, 5, 20, 10),
            'end_time': datetime(2026, 5, 20, 11),
        })
        assert result['success'] is True

    def test_accepts_iso_string_dates(self):
        result = self.logic.validate_schedule({
            'title': 'Meeting',
            'start_time': '2026-05-20T10:00:00',
            'end_time': '2026-05-20T11:00:00',
        })
        assert result['success'] is True

    def test_rejects_invalid_date_format(self):
        result = self.logic.validate_schedule({
            'title': 'Meeting',
            'start_time': 'not-a-time',
            'end_time': '2026-05-20T11:00:00',
        })
        assert result['success'] is False
        assert 'date' in result['message'].lower()


class TestCheckConflicts:
    def setup_method(self):
        self.logic = ScheduleLogic()

    def test_no_conflict_with_empty_list(self):
        new = {'start_time': datetime(2026, 5, 20, 10), 'end_time': datetime(2026, 5, 20, 11)}
        assert self.logic.check_conflicts([], new) is False

    def test_no_conflict_when_adjacent(self):
        existing = [FakeSchedule(datetime(2026, 5, 20, 9), datetime(2026, 5, 20, 10))]
        new = {'start_time': datetime(2026, 5, 20, 10), 'end_time': datetime(2026, 5, 20, 11)}
        assert self.logic.check_conflicts(existing, new) is False

    def test_conflict_when_overlapping(self):
        existing = [FakeSchedule(datetime(2026, 5, 20, 9), datetime(2026, 5, 20, 10, 30))]
        new = {'start_time': datetime(2026, 5, 20, 10), 'end_time': datetime(2026, 5, 20, 11)}
        assert self.logic.check_conflicts(existing, new) is True

    def test_conflict_when_new_contains_existing(self):
        existing = [FakeSchedule(datetime(2026, 5, 20, 10, 30), datetime(2026, 5, 20, 10, 45))]
        new = {'start_time': datetime(2026, 5, 20, 10), 'end_time': datetime(2026, 5, 20, 11)}
        assert self.logic.check_conflicts(existing, new) is True
