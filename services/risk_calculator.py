class RiskCalculator:

    # ==========================================
    # CONFIGURATION
    # ==========================================

    ATTENDANCE_THRESHOLDS = {

        "critical": 50,
        "poor": 65,
        "warning": 75,
        "monitor": 85
    }

    HOMEWORK_THRESHOLDS = {

        "critical": 3,
        "poor": 2,
        "warning": 1
    }

    ASSESSMENT_THRESHOLDS = {

        "critical": 40,
        "poor": 60,
        "warning": 80
    }

    # ==========================================
    # ATTENDANCE
    # ==========================================

    @classmethod
    def attendance_score(
        cls,
        student
    ):

        percentage = (
            student.get(
                "attendance_percentage",
                100
            ) or 100
        )

        score = 0

        reasons = []

        if percentage < cls.ATTENDANCE_THRESHOLDS["critical"]:

            score = 40

            reasons.append(
                "Very low attendance"
            )

        elif percentage < cls.ATTENDANCE_THRESHOLDS["poor"]:

            score = 30

            reasons.append(
                "Low attendance"
            )

        elif percentage < cls.ATTENDANCE_THRESHOLDS["warning"]:

            score = 20

            reasons.append(
                "Attendance below target"
            )

        elif percentage < cls.ATTENDANCE_THRESHOLDS["monitor"]:

            score = 10

        return {

            "score": score,

            "reasons": reasons
        }

    # ==========================================
    # HOMEWORK
    # ==========================================

    @classmethod
    def homework_score(
        cls,
        student
    ):

        overdue = (
            student.get(
                "overdue_homeworks",
                0
            ) or 0
        )

        pending = (
            student.get(
                "pending_homeworks",
                0
            ) or 0
        )

        score = 0

        reasons = []

        if overdue >= cls.HOMEWORK_THRESHOLDS["critical"]:

            score = 30

            reasons.append(
                "Multiple overdue homework"
            )

        elif overdue >= cls.HOMEWORK_THRESHOLDS["poor"]:

            score = 20

            reasons.append(
                "Overdue homework"
            )

        elif overdue >= cls.HOMEWORK_THRESHOLDS["warning"]:

            score = 10

        if pending >= 10:

            score += 5

            reasons.append(
                "Large homework backlog"
            )

        return {

            "score": score,

            "reasons": reasons
        }

    # ==========================================
    # ASSESSMENT
    # ==========================================

    @classmethod
    def assessment_score(
        cls,
        student
    ):

        average = (
            student.get(
                "average_percentage",
                100
            ) or 100
        )

        low_scores = (
            student.get(
                "low_score_count",
                0
            ) or 0
        )

        score = 0

        reasons = []

        if average < cls.ASSESSMENT_THRESHOLDS["critical"]:

            score = 30

            reasons.append(
                "Poor assessment performance"
            )

        elif average < cls.ASSESSMENT_THRESHOLDS["poor"]:

            score = 20

            reasons.append(
                "Below average assessment performance"
            )

        elif average < cls.ASSESSMENT_THRESHOLDS["warning"]:

            score = 10

        if low_scores >= 2:

            score += 10

            reasons.append(
                "Repeated low assessment scores"
            )

        return {

            "score": score,

            "reasons": reasons
        }

    # ==========================================
    # RISK LEVEL
    # ==========================================

    @staticmethod
    def risk_level(
        score
    ):

        if score >= 70:

            return "High"

        if score >= 40:

            return "Medium"

        return "Low"

    # ==========================================
    # MAIN CALCULATOR
    # ==========================================

    @classmethod
    def calculate(
        cls,
        student
    ):

        attendance = cls.attendance_score(
            student
        )

        homework = cls.homework_score(
            student
        )

        assessment = cls.assessment_score(
            student
        )

        score = (

            attendance["score"]

            + homework["score"]

            + assessment["score"]
        )

        reasons = (

            attendance["reasons"]

            + homework["reasons"]

            + assessment["reasons"]
        )

        return {

            "risk_score": score,

            "risk_level":
                cls.risk_level(score),

            "risk_breakdown": {

                "attendance":
                    attendance["score"],

                "homework":
                    homework["score"],

                "assessment":
                    assessment["score"]
            },

            "reasons": reasons
        }