from intents.student.enums import (
    StudentIntent
)

from db.session import (
    AsyncSessionLocal
)

from db.repositories.student.atlas_repository import (
    AtlasRepository
)


class AtlasTool:

    IMPLEMENTED_METRICS = {

        "academic": [
            "subject_grade_score",
            "homework_quality_score",
            "exam_readiness_score"
        ],

        "growth": [
            "attendance_score",
            "consistency_score",
            "conduct_score"
        ],

        "initiative": [
            "contribution_score"
        ]
    }

    async def run(
        self,
        context,
        parsed_intent
    ):

        if not context.enrollment_id:

            return {
                "error":
                    "Enrollment ID missing"
            }

        async with AsyncSessionLocal() as db:

            repo = AtlasRepository(
                db
            )

            atlas = (
                await repo.build_atlas_payload(
                    context.enrollment_id
                )
            )

            if not atlas:

                return {
                    "error":
                        "No atlas data found"
                }

            score = atlas["score"]

            pillars = atlas["pillars"]

            academic = pillars.get(
                "academic",
                {}
            )

            growth = pillars.get(
                "growth",
                {}
            )

            initiative = pillars.get(
                "initiative",
                {}
            )

            academic_score = (
                academic.get(
                    "score",
                    0
                )
            )

            growth_score = (
                growth.get(
                    "score",
                    0
                )
            )

            initiative_score = (
                initiative.get(
                    "score",
                    0
                )
            )

            # =====================================
            # OVERALL PILLARS
            # =====================================

            all_pillar_scores = {

                "academic":
                    academic_score,

                "growth":
                    growth_score,

                "initiative":
                    initiative_score
            }

            strongest_pillar = max(
                all_pillar_scores,
                key=all_pillar_scores.get
            )

            # =====================================
            # ACTIONABLE PILLARS
            # =====================================

            actionable_pillars = {

                "academic":
                    academic_score,

                "growth":
                    growth_score
            }

            strongest_actionable_pillar = max(
                actionable_pillars,
                key=actionable_pillars.get
            )

            weakest_actionable_pillar = min(
                actionable_pillars,
                key=actionable_pillars.get
            )

            # =====================================
            # INSIGHTS
            # =====================================

            insights = []

            recommended_focus = []

            if (
                academic.get(
                    "homework_quality_score",
                    0
                )
                <
                academic.get(
                    "subject_grade_score",
                    0
                )
            ):

                insights.append(
                    "Homework quality is lower than subject grades."
                )

                recommended_focus.append(
                    "homework_quality_score"
                )

            if (
                growth.get(
                    "attendance_score",
                    0
                )
                == 0
            ):

                insights.append(
                    "Attendance score is currently 0."
                )

                recommended_focus.append(
                    "attendance_score"
                )

            if (
                growth.get(
                    "consistency_score",
                    0
                )
                < 70
            ):

                insights.append(
                    "Consistency score is below target."
                )

                recommended_focus.append(
                    "consistency_score"
                )

            if (
                growth.get(
                    "conduct_score",
                    0
                )
                < 80
            ):

                insights.append(
                    "Conduct score has room for improvement."
                )

                recommended_focus.append(
                    "conduct_score"
                )

            # =====================================
            # SCORE CALIBRATION
            # =====================================

            atlas_score = score

            if (
                score.get(
                    "snapshot_date"
                ) is None
            ):

                atlas_score = {

                    "status":
                        "calibrating",

                    "message":
                        (
                            "Atlas Score is currently "
                            "calibrating. Your first "
                            "weekly Atlas Score will "
                            "be available next week."
                        )
                }

            payload = {

                "atlas_score":
                    atlas_score,

                "pillars":
                    pillars,

                "strongest_pillar":
                    strongest_pillar,

                "strongest_actionable_pillar":
                    strongest_actionable_pillar,

                "weakest_actionable_pillar":
                    weakest_actionable_pillar,

                "implemented_metrics":
                    self.IMPLEMENTED_METRICS,

                "insights":
                    insights,

                "recommended_focus":
                    recommended_focus,

                "performance_summary": {

                    "strongest":
                        strongest_actionable_pillar,

                    "weakest":
                        weakest_actionable_pillar,

                    "focus":
                        recommended_focus,

                    "insights":
                        insights,

                    "message":
                        (
                            f"{weakest_actionable_pillar} "
                            "is currently the weakest "
                            "actionable pillar."
                        )
                }
            }

            query = (
                getattr(
                    parsed_intent,
                    "original_query",
                    ""
                )
                .lower()
            )

            # =====================================
            # DIRECT ANSWERS
            # =====================================

            if any(
                phrase in query
                for phrase in [
                    "weakest pillar",
                    "which pillar is weakest"
                ]
            ):

                payload[
                    "direct_answer"
                ] = (
                    f"{weakest_actionable_pillar} "
                    "is currently the weakest "
                    "actionable pillar."
                )

            elif any(
                phrase in query
                for phrase in [
                    "strongest pillar",
                    "which pillar is strongest"
                ]
            ):

                payload[
                    "direct_answer"
                ] = (
                    f"{strongest_actionable_pillar} "
                    "is currently the strongest "
                    "actionable pillar."
                )

            # =====================================
            # PERFORMANCE ANALYSIS
            # =====================================

            if (
                parsed_intent.intent
                ==
                StudentIntent.STUDENT_PERFORMANCE
            ):

                payload[
                    "performance_analysis"
                ] = True

            return payload