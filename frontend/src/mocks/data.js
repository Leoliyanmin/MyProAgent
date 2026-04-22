// Mock data for MSW
// This file contains all mock data for the API endpoints

export const mockUser = {
  id: 1,
  email: 'test@example.com',
  full_name: '测试用户',
  avatar: null,
  created_at: '2024-01-01T00:00:00Z'
}

export const mockTasks = [
  {
    id: 1,
    title: 'Draft ECCV methodology section',
    description: 'Write the methodology section for ECCV paper',
    completed: false,
    priority: 0,
    color: '#ff3b30',
    due_date: '2026-04-20T10:00:00Z',
    created_at: '2026-04-15T08:00:00Z'
  },
  {
    id: 2,
    title: 'CS305 Matrix operations assignment',
    description: 'Complete matrix operations homework',
    completed: false,
    priority: 3,
    color: '#34c759',
    due_date: '2026-04-22T23:59:59Z',
    created_at: '2026-04-15T09:00:00Z'
  },
  {
    id: 3,
    title: 'Team meeting preparation',
    description: 'Prepare slides for weekly team meeting',
    completed: true,
    priority: 2,
    color: '#007aff',
    due_date: '2026-04-16T14:00:00Z',
    created_at: '2026-04-14T10:00:00Z'
  }
]

export const mockSchedules = [
  {
    id: 1,
    title: 'Morning Standup',
    description: 'Daily team sync',
    start_time: '2026-04-18T09:00:00Z',
    end_time: '2026-04-18T09:30:00Z',
    is_all_day: false,
    location: 'Zoom',
    color: '#007aff'
  },
  {
    id: 2,
    title: 'Project Review',
    description: 'Review project progress with stakeholders',
    start_time: '2026-04-18T14:00:00Z',
    end_time: '2026-04-18T15:30:00Z',
    is_all_day: false,
    location: 'Conference Room A',
    color: '#ff9500'
  },
  {
    id: 3,
    title: 'Team Building Event',
    description: 'Quarterly team building activity',
    start_time: '2026-04-19T00:00:00Z',
    end_time: '2026-04-19T23:59:59Z',
    is_all_day: true,
    location: 'Park',
    color: '#34c759'
  }
]

export const mockAgentHistory = [
  {
    id: 1,
    session_id: 'session-001',
    role: 'user',
    message: 'Help me organize my tasks for today',
    created_at: '2026-04-18T08:30:00Z'
  },
  {
    id: 2,
    session_id: 'session-001',
    role: 'assistant',
    message: 'I can see you have 3 pending tasks. Here\'s my suggestion:\n\n1. **Draft ECCV methodology section** (High Priority - Red)\n   - Due: April 20th\n   - Suggestion: Start with the experimental setup\n\n2. **CS305 Matrix operations assignment** (Medium Priority - Green)\n   - Due: April 22nd\n   - Suggestion: Focus on eigenvalue problems first\n\nWould you like me to create a study plan for these?',
    created_at: '2026-04-18T08:30:05Z'
  }
]

export const mockStudyPlan = {
  plan: [
    {
      time: '09:00 - 11:00',
      activity: 'Deep work: ECCV methodology',
      focus: 'High priority task'
    },
    {
      time: '14:00 - 15:30',
      activity: 'CS305 assignment - Matrix operations',
      focus: 'Practice problems'
    },
    {
      time: '16:00 - 17:00',
      activity: 'Review and planning',
      focus: 'Prepare for tomorrow'
    }
  ],
  generated_at: '2026-04-18T08:30:00Z'
}

export const mockToken = 'mock-jwt-token-for-development-only'

export const mockHeatmapData = {
  '2026-03-08': 3,
  '2026-03-09': 8,
  '2026-03-10': 5,
  '2026-03-11': 12,
  '2026-03-12': 6,
  '2026-03-13': 9,
  '2026-03-14': 4,
  '2026-03-15': 7,
  '2026-03-16': 10,
  '2026-03-17': 3,
  '2026-03-18': 8,
  '2026-03-19': 5,
  '2026-03-20': 12,
  '2026-03-21': 6,
  '2026-03-22': 9,
  '2026-03-23': 4,
  '2026-03-24': 7,
  '2026-03-25': 10,
  '2026-03-26': 3,
  '2026-03-27': 8,
  '2026-03-28': 5,
  '2026-03-29': 12,
  '2026-03-30': 6,
  '2026-03-31': 9,
  '2026-04-01': 4,
  '2026-04-02': 7,
  '2026-04-03': 10,
  '2026-04-04': 3,
  '2026-04-05': 8,
  '2026-04-06': 5,
  '2026-04-07': 12,
  '2026-04-08': 6,
  '2026-04-09': 9,
  '2026-04-10': 4,
  '2026-04-11': 7,
  '2026-04-12': 10,
  '2026-04-13': 3,
  '2026-04-14': 8,
  '2026-04-15': 5,
  '2026-04-16': 12,
  '2026-04-17': 6,
  '2026-04-18': 9
}
