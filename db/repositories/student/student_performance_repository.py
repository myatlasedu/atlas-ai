from db.repositories.student.assessment_repository import (
    AssessmentRepository
)

from db.repositories.student.attendance_repository import (
    AttendanceRepository
)

from db.repositories.student.homework_repository import (
    HomeworkRepository
)

from db.repositories.student.subject_repository import (
    SubjectRepository
)

from db.repositories.student.atlas_repository import (
    AtlasRepository
)


class StudentPerformanceRepository:

    def __init__(
        self,
        db
    ):

        self.db = db

        self.assessment_repo = (
            AssessmentRepository(db)
        )

        self.attendance_repo = (
            AttendanceRepository(db)
        )

        self.homework_repo = (
            HomeworkRepository(db)
        )

        self.subject_repo = (
            SubjectRepository(db)
        )

        self.atlas_repo = (
            AtlasRepository(db)
        )

    async def get_performance_data(
        self,
        enrollment_id
    ):

        attendance = (
            await self.attendance_repo.get_attendance_percentage(
                enrollment_id
            )
        )

        pending_homework = (
            await self.homework_repo.get_pending_homework(
                enrollment_id
            )
        )

        overdue_homework = (
            await self.homework_repo.get_overdue_homework(
                enrollment_id
            )
        )

        assessment_summary = (
            await self.assessment_repo.get_performance_summary(
                enrollment_id
            )
        )

        assessment_consistency = (
            await self.assessment_repo.get_consistency_metrics(
                enrollment_id
            )
        )

        assessment_risks = (
            await self.assessment_repo.get_risk_assessments(
                enrollment_id
            )
        )

        highest_assessment = (
            await self.assessment_repo.get_highest_scoring_assessment(
                enrollment_id
            )
        )

        lowest_assessment = (
            await self.assessment_repo.get_lowest_scoring_assessment(
                enrollment_id
            )
        )

        strongest_subject = (
            await self.subject_repo.get_strongest_subject(
                enrollment_id
            )
        )

        weakest_subject = (
            await self.subject_repo.get_weakest_subject(
                enrollment_id
            )
        )

        atlas = (
            await self.atlas_repo.build_atlas_payload(
                enrollment_id
            )
        )

        atlas_available = False
        atlas_score = None
        pillars = {}
        strongest_pillar = None
        weakest_pillar = None

        if atlas:

            atlas_available = atlas is not None

            atlas_score = atlas.get(
                "atlas"
            )

            pillars = atlas.get(
                "pillars"
            ) or {}

            if pillars:

                pillar_scores = {

                    name: value["score"]

                    for name, value

                    in pillars.items()
                }

                strongest_pillar = max(

                    pillar_scores,

                    key=pillar_scores.get
                )

                weakest_pillar = min(

                    pillar_scores,

                    key=pillar_scores.get
                )

        # ======================================================
        # RISK SIGNALS
        # ======================================================

        signals = {

            "attendance": {

                "at_risk":

                    attendance.get(
                        "attendance_percentage",
                        0
                    ) < 75,

                "attendance_percentage":

                    attendance.get(
                        "attendance_percentage",
                        0
                    )
            },

            "homework": {

                "at_risk":

                    len(
                        overdue_homework
                    ) >= 3,

                "pending_count":

                    len(
                        pending_homework
                    ),

                "overdue_count":

                    len(
                        overdue_homework
                    )
            },

            "assessment": {

                "at_risk":

                    len(
                        assessment_risks
                    ) > 0,

                "risk_count":

                    len(
                        assessment_risks
                    ),

                "consistency":

                    assessment_consistency.get(
                        "rating"
                    )
            },

            "atlas": {

                "available":
                    atlas_available,

                "at_risk":

                    (
                        atlas_available
                        and
                        atlas_score
                        and
                        atlas_score["score"] < 60
                    )
            }
        }

        # ======================================================
        # STRENGTHS
        # ======================================================

        strengths = []

        if strongest_subject:

            strengths.append({

                "type":
                    "subject",

                "value":
                    strongest_subject
            })

        if highest_assessment:

            strengths.append({

                "type":
                    "assessment",

                "value":
                    highest_assessment
            })

        if atlas_available and strongest_pillar:

            strengths.append({

                "type":
                    "atlas",

                "pillar":
                    strongest_pillar,

                "score":

                    pillars[
                        strongest_pillar
                    ]["score"]
            })

        # ======================================================
        # WEAKNESSES
        # ======================================================

        weaknesses = []

        if weakest_subject:

            weaknesses.append({

                "type":
                    "subject",

                "value":
                    weakest_subject
            })

        if lowest_assessment:

            weaknesses.append({

                "type":
                    "assessment",

                "value":
                    lowest_assessment
            })

        if atlas_available and weakest_pillar:

            weaknesses.append({

                "type":
                    "atlas",

                "pillar":
                    weakest_pillar,

                "score":

                    pillars[
                        weakest_pillar
                    ]["score"]
            })

        if signals["attendance"]["at_risk"]:

            weaknesses.append({

                "type":
                    "attendance"
            })

        if signals["homework"]["at_risk"]:

            weaknesses.append({

                "type":
                    "homework"
            })

        # ======================================================
        # RECOMMENDED FOCUS
        # ======================================================

        recommended_focus = []

        if atlas_available and weakest_pillar:

            recommended_focus.append({

                "type":
                    "atlas",

                "pillar":
                    weakest_pillar
            })

        if weakest_subject:

            recommended_focus.append({

                "type":
                    "subject",

                "value":
                    weakest_subject
            })

        if assessment_risks:

            recommended_focus.append({

                "type":
                    "assessment",

                "value":
                    assessment_risks[:3]
            })

        if signals["attendance"]["at_risk"]:

            recommended_focus.append({

                "type":
                    "attendance"
            })

        if signals["homework"]["at_risk"]:

            recommended_focus.append({

                "type":
                    "homework"
            })
        return {

            # ==================================================
            # RAW DATA (FOR UI)
            # ==================================================

            "attendance":
                attendance,

            "homework": {

                "pending_count":
                    len(
                        pending_homework
                    ),

                "overdue_count":
                    len(
                        overdue_homework
                    ),

                "pending":
                    pending_homework,

                "overdue":
                    overdue_homework
            },

            "assessment": {

                "summary":
                    assessment_summary,

                "consistency":
                    assessment_consistency,

                "risks":
                    assessment_risks,

                "highest":
                    highest_assessment,

                "lowest":
                    lowest_assessment
            },

            "subjects": {

                "strongest":
                    strongest_subject,

                "weakest":
                    weakest_subject
            },

            "atlas":
                atlas,

            "signals":
                signals,

            # ==================================================
            # LLM READY
            # ==================================================

            "llm_summary": {

                "overall_status":

                    (
                        "Needs Attention"

                        if (
                            signals["attendance"]["at_risk"]
                            or
                            signals["homework"]["at_risk"]
                            or
                            signals["assessment"]["at_risk"]
                            or
                            signals["atlas"]["at_risk"]
                        )

                        else "Healthy"
                    ),

                "strengths": [

                    item

                    for item in [

                        (
                            f"Attendance is "
                            f"{attendance.get('attendance_percentage', 0)}%."
                        )

                        if (
                            attendance.get(
                                "attendance_percentage",
                                0
                            ) >= 90
                        )

                        else None,

                        (
                            f"Strongest subject is "
                            f"{strongest_subject['subject_name']}."
                        )

                        if strongest_subject

                        else None,

                        (
                            f"Best assessment was "
                            f"{highest_assessment['title']} "
                            f"({highest_assessment['percentage']}%)."
                        )

                        if highest_assessment

                        else None,

                        (
                            f"Strongest Atlas pillar is "
                            f"{strongest_pillar.title()}."
                        )

                        if (
                            atlas_available
                            and
                            strongest_pillar
                        )

                        else None
                    ]

                    if item is not None
                ],

                "concerns": [

                    item

                    for item in [

                        (
                            f"{len(overdue_homework)} overdue homework assignment(s)."
                        )

                        if overdue_homework

                        else None,

                        (
                            f"{len(pending_homework)} pending homework assignment(s)."
                        )

                        if pending_homework

                        else None,

                        (
                            f"Weakest subject is "
                            f"{weakest_subject['subject_name']}."
                        )

                        if weakest_subject

                        else None,

                        (
                            f"Lowest assessment was "
                            f"{lowest_assessment['title']} "
                            f"({lowest_assessment['percentage']}%)."
                        )

                        if lowest_assessment

                        else None,

                        (
                            f"Weakest Atlas pillar is "
                            f"{weakest_pillar.title()}."
                        )

                        if (
                            atlas_available
                            and
                            weakest_pillar
                        )

                        else None
                    ]

                    if item is not None
                ],

                "recommended_actions": [

                    item

                    for item in [

                        "Improve attendance."

                        if signals["attendance"]["at_risk"]

                        else None,

                        "Complete overdue homework."

                        if signals["homework"]["at_risk"]

                        else None,

                        "Review recent assessment performance."

                        if signals["assessment"]["at_risk"]

                        else None,

                        (
                            f"Focus on {weakest_subject['subject_name']}."
                        )

                        if weakest_subject

                        else None,

                        (
                            f"Improve the "
                            f"{weakest_pillar.title()} pillar."
                        )

                        if (
                            atlas_available
                            and
                            weakest_pillar
                        )

                        else None
                    ]

                    if item is not None
                ],

                "atlas_status":

                    (
                        "Available"

                        if atlas_available

                        else "Calibrating"
                    )
            },

            # ==================================================
            # LEGACY FIELDS
            # ==================================================

            "strengths":
                strengths,

            "weaknesses":
                weaknesses,

            "recommended_focus":
                recommended_focus
        }