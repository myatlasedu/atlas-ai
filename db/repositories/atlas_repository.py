from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class AtlasRepository:

    def __init__(
        self,
        db: AsyncSession
    ):
        self.db = db

    # =====================================================
    # LATEST SNAPSHOT
    # =====================================================

    async def get_latest_snapshot(
        self,
        enrollment_id: int
    ):

        query = text(
            """
            SELECT *

            FROM analytics_student_daily_atlas_score

            WHERE enrollment_id = :enrollment_id

            ORDER BY snapshot_date DESC

            LIMIT 1
            """
        )

        result = await self.db.execute(
            query,
            {
                "enrollment_id": enrollment_id
            }
        )

        row = (
            result
            .mappings()
            .first()
        )

        if not row:
            return None

        return dict(row)

    # =====================================================
    # BUILD COMPLETE ATLAS PAYLOAD
    # =====================================================

    async def build_atlas_payload(
        self,
        enrollment_id: int
    ):

        latest = await self.get_latest_snapshot(
            enrollment_id
        )

        if not latest:
            return None

        score = {

            "score":
                float(
                    latest.get(
                        "display_atlas_score"
                    )
                    or 0
                ),

            "band":
                latest.get(
                    "display_atlas_band"
                ),

            "snapshot_date":
                latest.get(
                    "display_atlas_snapshot_date"
                )
        }

        pillars = {

            "academic": {

                "score":
                    float(
                        latest.get(
                            "academic_score",
                            0
                        )
                    ),

                "subject_grade_score":
                    latest.get(
                        "subject_grade_score",
                        0
                    ),

                "homework_quality_score":
                    latest.get(
                        "homework_quality_score",
                        0
                    ),

                "exam_readiness_score":
                    latest.get(
                        "exam_readiness_score",
                        0
                    )
            },

            "growth": {

                "score":
                    float(
                        latest.get(
                            "growth_score",
                            0
                        )
                    ),

                "attendance_score":
                    latest.get(
                        "attendance_score",
                        0
                    ),

                "consistency_score":
                    latest.get(
                        "consistency_score",
                        0
                    ),

                "conduct_score":
                    latest.get(
                        "conduct_score",
                        0
                    )
            },

            "initiative": {

                "score":
                    float(
                        latest.get(
                            "initiative_score",
                            0
                        )
                    ),

                "curiosity_score":
                    latest.get(
                        "curiosity_score",
                        0
                    ),

                "preparation_score":
                    latest.get(
                        "preparation_score",
                        0
                    ),

                "contribution_score":
                    latest.get(
                        "contribution_score",
                        0
                    ),

                "extracurricular_score":
                    latest.get(
                        "extracurricular_score",
                        0
                    )
            }
        }

        return {

            "score":
                score,

            "pillars":
                pillars,

            "raw":
                latest
        }