"""LocalAgent tools module."""

import sys
from pathlib import Path

# Ensure the project root is on sys.path so that all tool files can
# uniformly import from local_backend.* without try/except fallbacks.
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from .base import BaseTool, ToolRegistry
from .file_tools import ReadFileTool, WriteFileTool, EditFileTool
from .dir_tools import ListDirTool, CreateDirTool
from .search_tools import SearchFilesTool, GrepTool
from .file_ops import MoveFileTool, DeleteFileTool, CopyFileTool
from .shell_tool import ExecTool
from .calendar_tools import (
    CreateScheduleEventTool,
    UpdateScheduleEventTool,
    UpdateScheduleEventTimeTool,
    DeleteScheduleEventTool,
)
from .email_tools import (
    AnalyzeEmailsTool,
    CheckEmailStatusTool,
    DeleteEmailTool,
    EmptyTrashTool,
    GetEmailsTool,
    GetStarredEmailsTool,
    GetTrashEmailsTool,
    PermanentDeleteEmailTool,
    RestoreEmailTool,
    SendEmailTool,
    StarEmailTool,
    SyncEmailsTool,
    UnstarEmailTool,
)
from .profile_tools import GetUserProfileTool
from .task_tools import (
    ListTasksTool,
    CreateTaskTool,
    UpdateTaskTool,
    DeleteTaskTool,
)

__all__ = [
    "BaseTool",
    "ToolRegistry",
    "ReadFileTool",
    "WriteFileTool",
    "EditFileTool",
    "ListDirTool",
    "CreateDirTool",
    "SearchFilesTool",
    "GrepTool",
    "MoveFileTool",
    "DeleteFileTool",
    "CopyFileTool",
    "ExecTool",
    "CreateScheduleEventTool",
    "UpdateScheduleEventTool",
    "UpdateScheduleEventTimeTool",
    "DeleteScheduleEventTool",
    "CheckEmailStatusTool",
    "DeleteEmailTool",
    "EmptyTrashTool",
    "GetEmailsTool",
    "GetStarredEmailsTool",
    "GetTrashEmailsTool",
    "PermanentDeleteEmailTool",
    "RestoreEmailTool",
    "SendEmailTool",
    "StarEmailTool",
    "SyncEmailsTool",
    "UnstarEmailTool",
    "AnalyzeEmailsTool",
    "GetUserProfileTool",
    "GetBlackboardStatusTool",
    "SyncBlackboardTool",
    "GetBlackboardAssignmentsTool",
    "GetTisStatusTool",
    "GetTisScheduleTool",
    "ListCoursesTool",
    "ListTasksTool",
    "CreateTaskTool",
    "UpdateTaskTool",
    "DeleteTaskTool",
]
