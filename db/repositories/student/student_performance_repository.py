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
            await self.attendance_repo
            .get_attendance_percentage(
                enrollment_id
            )
        )

        pending_homework = (
            await self.homework_repo
            .get_pending_homework(
                enrollment_id
            )
        )

        overdue_homework = (
            await self.homework_repo
            .get_overdue_homework(
                enrollment_id
            )
        )

        assessment_summary = (
            await self.assessment_repo
            .get_performance_summary(
                enrollment_id
            )
        )

        assessment_consistency = (
            await self.assessment_repo
            .get_consistency_metrics(
                enrollment_id
            )
        )

        assessment_risks = (
            await self.assessment_repo
            .get_risk_assessments(
                enrollment_id
            )
        )

        highest_assessment = (
            await self.assessment_repo
            .get_highest_scoring_assessment(
                enrollment_id
            )
        )

        lowest_assessment = (
            await self.assessment_repo
            .get_lowest_scoring_assessment(
                enrollment_id
            )
        )

        strongest_subject = (
            await self.subject_repo
            .get_strongest_subject(
                enrollment_id
            )
        )

        weakest_subject = (
            await self.subject_repo
            .get_weakest_subject(
                enrollment_id
            )
        )

        atlas = (
            await self.atlas_repo
            .build_atlas_payload(
                enrollment_id
            )
        )

        atlas_score = None
        atlas_pillars = None

        if atlas:

            atlas_score = atlas["score"]

            atlas_pillars = atlas["pillars"]

        strongest_pillar = None
        weakest_pillar = None

        if atlas_pillars:

            pillar_scores = {

                "academic":
                    atlas_pillars[
                        "academic"
                    ]["score"],

                "growth":
                    atlas_pillars[
                        "growth"
                    ]["score"],

                "initiative":
                    atlas_pillars[
                        "initiative"
                    ]["score"]
            }

            strongest_pillar = max(
                pillar_scores,
                key=pillar_scores.get
            )

            weakest_pillar = min(
                pillar_scores,
                key=pillar_scores.get
            )

        signals = {

            "attendance_risk":
                attendance.get(
                    "attendance_percentage",
                    0
                ) < 75,

            "homework_risk":
                len(
                    overdue_homework
                ) >= 3,

            "assessment_risk":
                len(
                    assessment_risks
                ) > 0,

            "consistency_risk":
                assessment_consistency.get(
                    "rating"
                )
                in [
                    "Moderate",
                    "Poor"
                ],

            "atlas_risk":
                (
                    atlas_score
                    and
                    atlas_score["score"] < 60
                )
        }

        strengths = []

        weaknesses = []

        recommended_focus = []

        # ==========================
        # STRENGTHS
        # ==========================

        if strongest_subject:

            strengths.append(
                f"Strongest subject: "
                f"{strongest_subject['subject_name']}"
            )

        if highest_assessment:

            strengths.append(
                f"Best assessment: "
                f"{highest_assessment['title']}"
            )

        if strongest_pillar:

            strengths.append(
                f"Strongest Atlas pillar: "
                f"{strongest_pillar.title()}"
            )

        # ==========================
        # WEAKNESSES
        # ==========================

        if weakest_subject:

            weaknesses.append(
                f"Weakest subject: "
                f"{weakest_subject['subject_name']}"
            )

        if lowest_assessment:

            weaknesses.append(
                f"Weakest assessment: "
                f"{lowest_assessment['title']}"
            )

        if weakest_pillar:

            weaknesses.append(
                f"Weakest Atlas pillar: "
                f"{weakest_pillar.title()}"
            )

        if signals["attendance_risk"]:

            weaknesses.append(
                "Attendance below target."
            )

        if signals["homework_risk"]:

            weaknesses.append(
                "Multiple overdue homework."
            )

        # ==========================
        # RECOMMENDED FOCUS
        # ==========================

        if weakest_pillar:

            recommended_focus.append(
                weakest_pillar.title()
            )

        if assessment_risks:

            recommended_focus.extend(
                [
                    item["title"]
                    for item
                    in assessment_risks[:3]
                ]
            )

        if (
            weakest_subject
            and
            weakest_subject[
                "subject_name"
            ]
            not in recommended_focus
        ):

            recommended_focus.append(
                weakest_subject[
                    "subject_name"
                ]
            )

        return {

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
                    )
            },

            "assessment": {

                "summary":
                    assessment_summary,

                "consistency":
                    assessment_consistency,

                "risk_count":
                    len(
                        assessment_risks
                    )
            },

            "subjects": {

                "strongest":
                    strongest_subject,

                "weakest":
                    weakest_subject
            },

            "atlas": {

                "score":
                    atlas_score,

                "pillars":
                    atlas_pillars,

                "strongest_pillar":
                    strongest_pillar,

                "weakest_pillar":
                    weakest_pillar
            },

            "signals":
                signals,

            "strengths":
                strengths,

            "weaknesses":
                weaknesses,

            "recommended_focus":
                recommended_focus
        }