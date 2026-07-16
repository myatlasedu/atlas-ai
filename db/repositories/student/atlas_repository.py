from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from utils import ist_today

class AtlasRepository:

    def __init__(
        self,
        db: AsyncSession,
    ):
        self.db = db

    # =====================================================
    # LATEST SNAPSHOT
    # =====================================================
    async def get_latest_snapshot(
        self,
        enrollment_id: int,
    ):

        query = text(
            """
            SELECT

                atlas.*,

                ay.atlas_calibration_end_date

            FROM analytics_student_daily_atlas_score atlas

            INNER JOIN schools_academicyear ay

                ON ay.id = atlas.academic_year_id

            WHERE

                atlas.enrollment_id = :enrollment_id

            ORDER BY

                atlas.snapshot_date DESC

            LIMIT 1
            """
        )

        result = await self.db.execute(

            query,

            {
                "enrollment_id": enrollment_id,
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
        enrollment_id: int,
    ):

        latest = await self.get_latest_snapshot(
            enrollment_id
        )

        if not latest:

            return None

        atlas_calibration_end_date = (
            latest.get(
                "atlas_calibration_end_date"
            )
        )

        is_calibrating = (

            atlas_calibration_end_date is not None

            and

            ist_today()
            <=
            atlas_calibration_end_date
        )

        atlas = {

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
                ),
        }

        pillars = {

            # =====================================================
            # Academic
            # =====================================================

            "academic": {

                "score":
                    float(
                        latest.get(
                            "display_academic_score"
                        )
                        or 0
                    ),

                "band":
                    latest.get(
                        "display_academic_band"
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
            },

            # =====================================================
            # Growth
            # =====================================================

            "growth": {

                "score":
                    float(
                        latest.get(
                            "display_growth_score"
                        )
                        or 0
                    ),

                "band":
                    latest.get(
                        "display_growth_band"
                    ),

                "progress_score":
                    latest.get(
                        "progress_score",
                        0
                    ),

                "consistency_score":
                    latest.get(
                        "consistency_score",
                        0
                    ),

                "planning_ahead_score":
                    latest.get(
                        "planning_ahead_score",
                        0
                    ),

                "journal_score":
                    latest.get(
                        "journal_score",
                        0
                    ),

                "personal_event_score":
                    latest.get(
                        "personal_event_score",
                        0
                    ),

                "journal_habit":
                    latest.get(
                        "journal_habit",
                        0
                    ),

                "personal_event_habit":
                    latest.get(
                        "personal_event_habit",
                        0
                    ),
            },

            # =====================================================
            # Engagement
            # =====================================================

            "engagement": {

                "score":
                    float(
                        latest.get(
                            "display_engagement_score"
                        )
                        or 0
                    ),

                "band":
                    latest.get(
                        "display_engagement_band"
                    ),

                "period_attendance_score":
                    latest.get(
                        "period_attendance_score",
                        0
                    ),

                "tentative_exam_preparation_score":
                    latest.get(
                        "tentative_exam_preparation_score",
                        0
                    ),

                "contribution_score":
                    latest.get(
                        "contribution_score",
                        0
                    ),

                "enrichment_attendance_score":
                    latest.get(
                        "enrichment_attendance_score",
                        0
                    ),
            },
        }

        return {

            "available":
                not is_calibrating,

            "is_calibrating":
                is_calibrating,

            "calibration_end_date":
                atlas_calibration_end_date,

            "message":
                (
                    "Atlas is currently calibrating. "
                    "Your Atlas Score and pillar insights "
                    "will become available after the "
                    "calibration period ends."
                )
                if is_calibrating
                else None,

            "atlas":
                {}
                if is_calibrating
                else atlas,

            "pillars":
                {}
                if is_calibrating
                else pillars,

            "raw":
                latest,
        }