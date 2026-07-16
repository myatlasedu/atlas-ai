from sqlalchemy import text


from sqlalchemy import text


class SubjectRepository:

    def __init__(
        self,
        db,
    ):
        self.db = db

    # =====================================================
    # SUBJECT PERFORMANCE
    # =====================================================

    async def get_subject_performance(
        self,
        enrollment_id,
    ):

        query = text(
            """
            SELECT
                subject_name,
                score,
                final_grade,
                attendance_percentage,
                homework_percentage,
                overall_comment
            FROM students_reportcardsubjectsnapshot
            WHERE enrollment_id = :enrollment_id
            ORDER BY score DESC
            """
        )

        result = await self.db.execute(
            query,
            {
                "enrollment_id": enrollment_id,
            },
        )

        subjects = [
            dict(row)
            for row in result.mappings().all()
        ]

        if not subjects:

            return {

                "subjects": [],

                "subject_count": 0,

                "average_score": 0,

                "highest_score": 0,

                "lowest_score": 0,

                "status": "building",

                "strongest_subject": None,

                "weakest_subject": None,

                "high_performing_subjects": 0,

                "needs_attention_subjects": 0,

                "insights": [
                    "No subject performance data is available yet."
                ],

                "recommended_focus": [],

                "recommended_actions": [],
            }

        # =====================================================
        # SUMMARY
        # =====================================================

        subject_count = len(subjects)

        strongest_subject = subjects[0]

        weakest_subject = subjects[-1]

        scores = [

            float(
                subject.get("score") or 0
            )

            for subject in subjects
        ]

        average_score = round(

            sum(scores)
            /
            subject_count,

            2,
        )

        highest_score = max(scores)

        lowest_score = min(scores)

        # =====================================================
        # STATUS
        # =====================================================

        if average_score >= 90:

            status = "excellent"

        elif average_score >= 75:

            status = "good"

        elif average_score >= 60:

            status = "attention"

        else:

            status = "critical"

        # =====================================================
        # COUNTS
        # =====================================================

        high_performing_subjects = sum(

            1

            for score in scores

            if score >= 75
        )

        needs_attention_subjects = sum(

            1

            for score in scores

            if score < 60
        )

        # =====================================================
        # INSIGHTS
        # =====================================================

        insights = [

            (
                f"Your strongest subject is "
                f"{strongest_subject['subject_name']} "
                f"({strongest_subject['score']})."
            ),

            (
                f"{weakest_subject['subject_name']} "
                f"is currently your lowest scoring subject."
            ),
        ]

        recommended_focus = []

        recommended_actions = []

        if needs_attention_subjects:

            recommended_focus.append(
                weakest_subject["subject_name"]
            )

            recommended_actions.append(
                f"Spend additional revision time on "
                f"{weakest_subject['subject_name']}."
            )

        if average_score < 75:

            recommended_actions.append(
                "Aim to improve consistency across all subjects."
            )

        return {

            "subjects":
                subjects,

            "subject_count":
                subject_count,

            "average_score":
                average_score,

            "highest_score":
                highest_score,

            "lowest_score":
                lowest_score,

            "status":
                status,

            "strongest_subject":
                strongest_subject,

            "weakest_subject":
                weakest_subject,

            "high_performing_subjects":
                high_performing_subjects,

            "needs_attention_subjects":
                needs_attention_subjects,

            "insights":
                insights,

            "recommended_focus":
                recommended_focus,

            "recommended_actions":
                recommended_actions,
        }

    # =====================================================
    # STRONGEST SUBJECT
    # =====================================================

    async def get_strongest_subject(
        self,
        enrollment_id,
    ):

        payload = await self.get_subject_performance(
            enrollment_id
        )

        return payload.get(
            "strongest_subject"
        )

    # =====================================================
    # WEAKEST SUBJECT
    # =====================================================

    async def get_weakest_subject(
        self,
        enrollment_id,
    ):

        payload = await self.get_subject_performance(
            enrollment_id
        )

        return payload.get(
            "weakest_subject"
        )