from tools.student.attendance_tool import (
    AttendanceTool
)
from tools.student.atlas_tool import (
    AtlasTool
)
from tools.student.homework_tool import (
    HomeworkTool
)
from tools.student.assessment_tool import (
    AssessmentTool
)

from tools.student.announcement_tool import (
    AnnouncementTool
)

from tools.student.forum_tool import (
    ForumTool
)

from tools.student.subject_tool import (
    SubjectTool
)

from tools.student.topic_tool import (
    TopicTool
)

from tools.student.student_performance_tool import (
    StudentPerformanceTool
)

from tools.student.personal_event_create_tool import PersonalEventCreateTool

from tools.student.personal_event_tool import PersonalEventTool

from tools.student.action_executor_tool import ActionExecutorTool

from tools.student.journal_tool import (
    JournalTool
)

from tools.student.journal_create_tool import (
    JournalCreateTool
)

from tools.student.screen_navigation_tool import (
    ScreenNavigationTool
)

from tools.student.calendar_tool import (
    CalendarTool
)

TOOL_REGISTRY = {

    "screen_navigation_tool": ScreenNavigationTool(),

    "atlas_tool": AtlasTool(),

    "attendance_tool": AttendanceTool(),

    "homework_tool": HomeworkTool(),

    "assessment_tool": AssessmentTool(),

    "announcement_tool": AnnouncementTool(),

    "calendar_tool": CalendarTool(),
    
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