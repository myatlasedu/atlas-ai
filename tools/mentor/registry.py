from tools.mentor.attendance_tool import (
    AttendanceTool
)

# Future imports
from tools.mentor.homework_tool import HomeworkTool
from tools.mentor.assessment_tool import AssessmentTool
# from tools.mentor.student_analysis_tool import StudentAnalysisTool
# from tools.mentor.grading_tool import GradingTool
# from tools.mentor.timetable_tool import TimetableTool
# from tools.mentor.dashboard_tool import DashboardTool


TOOL_REGISTRY = {

    "attendance_tool":
        AttendanceTool(),

    "homework_tool":
        HomeworkTool(),

    "assessment_tool":
        AssessmentTool(),

    # "student_analysis_tool":
    #     StudentAnalysisTool(),

    # "grading_tool":
    #     GradingTool(),

    # "timetable_tool":
    #     TimetableTool(),

    # "dashboard_tool":
    #     DashboardTool(),

}