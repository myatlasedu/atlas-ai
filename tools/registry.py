from tools.attendance_tool import (
    AttendanceTool
)
from tools.atlas_tool import (
    AtlasTool
)
from tools.homework_tool import (
    HomeworkTool
)
from tools.assessment_tool import (
    AssessmentTool
)

from tools.announcement_tool import (
    AnnouncementTool
)

from tools.forum_tool import (
    ForumTool
)

from tools.subject_tool import (
    SubjectTool
)

from tools.topic_tool import (
    TopicTool
)

from tools.student_performance_tool import (
    StudentPerformanceTool
)

from tools.personal_event_create_tool import PersonalEventCreateTool

from tools.personal_event_tool import PersonalEventTool

from tools.action_executor_tool import ActionExecutorTool

from tools.journal_tool import (
    JournalTool
)

from tools.journal_create_tool import (
    JournalCreateTool
)

from tools.screen_navigation_tool import (
    ScreenNavigationTool
)

TOOL_REGISTRY = {

    "screen_navigation_tool": ScreenNavigationTool(),

    "atlas_tool": AtlasTool(),

    "attendance_tool": AttendanceTool(),

    "homework_tool": HomeworkTool(),

    "assessment_tool": AssessmentTool(),

    "announcement_tool": AnnouncementTool(),
    
    "forum_tool": ForumTool(),

    "subject_tool": SubjectTool(),

    "topic_tool": TopicTool(),

    "student_performance_tool":
        StudentPerformanceTool(),

    "personal_event_tool": PersonalEventTool(),

    "personal_event_create_tool": PersonalEventCreateTool(),

    "action_executor_tool": ActionExecutorTool(),

    "journal_tool": JournalTool(),

    "journal_create_tool": JournalCreateTool()
    
}