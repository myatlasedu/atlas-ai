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

        if not context.enrollment_id:

            return {
                "error":
                    "Enrollment ID missing"
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

                    "error":
                        "Atlas data not found."
                }

            if atlas["is_calibrating"]:

                return {

                    "status":
                        "calibrating",

                    "message":
                        atlas["message"],

                    "calibration_end_date":
                        atlas["calibration_end_date"]
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

                payload["direct_answer"] = {
                    "pillar": weakest_pillar
                }

            elif any(
                phrase in query
                for phrase in [
                    "strongest pillar",
                    "best pillar",
                    "highest pillar",
                    "which pillar is strongest"
                ]
            ):

                payload["direct_answer"] = {
                    "pillar": strongest_pillar
                }

            return payload