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
        ],

        "growth": [

            "progress_score",

            "consistency_score",

            "planning_ahead_score",

            "journal_score",

            "personal_event_score",
        ],

        "engagement": [

            "period_attendance_score",

            "tentative_exam_preparation_score",

            "contribution_score",

            "enrichment_attendance_score",
        ],
    }

    async def run(
        self,
        context,
        parsed_intent
    ):

        # Guardians read about their child; students about themselves.

        owner = (
            "your child's"
            if getattr(context, "role", None) == "guardian"
            else "your"
        )

        if not context.enrollment_id:

            return {

                "module":
                    "atlas",

                "error":
                    "Enrollment ID missing",

                "direct_answer":
                    f"Unable to load {owner} Atlas Score.",
            }

        async with AsyncSessionLocal() as db:

            repo = AtlasRepository(
                db
            )

            atlas = await repo.build_atlas_payload(
                context.enrollment_id
            )

            if not atlas:

                return {

                    "module":
                        "atlas",

                    "error":
                        "Atlas data not found.",

                    "direct_answer":
                        f"{owner.capitalize()} Atlas Score is not available yet.",
                }

            if atlas["is_calibrating"]:

                return {

                    "module":
                        "atlas",

                    "status":
                        "calibrating",

                    "message":
                        atlas["message"],

                    "calibration_end_date":
                        atlas["calibration_end_date"],

                    "direct_answer": (
                        "Atlas is currently calibrating. "
                        f"{owner.capitalize()} Atlas Score and pillar "
                        "insights will become available after "
                        f"{atlas['calibration_end_date']}."
                    ),
                }

            atlas_score = atlas["atlas"]

            pillars = atlas["pillars"]

            pillar_scores = {

                name: pillar["score"]

                for name, pillar

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

            payload = {

                "module":
                    "atlas",

                "available": True,
                
                "atlas_score":
                    atlas_score,

                "pillars":
                    pillars,

                "strongest_pillar":
                    strongest_pillar,

                "weakest_pillar":
                    weakest_pillar,

                "implemented_metrics":
                    self.IMPLEMENTED_METRICS,

                "strengths": [

                    {
                        "pillar": strongest_pillar
                    }
                ],

                "recommended_focus": [

                    {
                        "pillar": weakest_pillar
                    }
                ]
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
                    "lowest pillar",
                    "which pillar is weakest",
                    "which pillar needs improvement"
                ]
            ):

                payload["direct_answer"] = (
                    f"{owner.capitalize()} weakest Atlas pillar is "
                    f"{weakest_pillar}."
                )

            elif any(
                phrase in query
                for phrase in [
                    "strongest pillar",
                    "best pillar",
                    "highest pillar",
                    "which pillar is strongest"
                ]
            ):

                payload["direct_answer"] = (
                    f"{owner.capitalize()} strongest Atlas pillar is "
                    f"{strongest_pillar}."
                )

            else:

                payload["llm_context"] = {

                    "atlas_score":
                        atlas_score,

                    "pillars":
                        pillars,

                    "strongest_actionable_pillar":
                        strongest_pillar,

                    "weakest_actionable_pillar":
                        weakest_pillar,
                }

            return payload