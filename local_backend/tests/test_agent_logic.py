import pytest
from business.agent_logic import AgentLogic


class TestAgentLogic:
    def setup_method(self):
        self.logic = AgentLogic()

    def test_process_query_returns_response(self):
        result = self.logic.process_query('user1', 'Hello', 'session1')
        assert 'response' in result
        assert 'Hello' in result['response']

    def test_process_query_returns_thought_trace(self):
        result = self.logic.process_query('user1', 'Hello', 'session1')
        assert isinstance(result['thought_trace'], list)
        assert len(result['thought_trace']) == 2

    def test_process_query_no_tool_calls_by_default(self):
        result = self.logic.process_query('user1', 'Hello', 'session1')
        assert result['tool_calls'] == []
        assert result['requires_confirmation'] is False
