import calendar
import logging
import re

from datetime import (
    date,
    datetime,
    timedelta,
)

from zoneinfo import (
    ZoneInfo,
    ZoneInfoNotFoundError,
)


logger = logging.getLogger(__name__)


class TemporalService:

    #
    # Existing behaviour was hard-coded to IST. That stays the
    # default so nothing changes for callers that never send a
    # timezone.
    #

    DEFAULT_TIMEZONE = "Asia/Kolkata"

    # ==================================================
    # TIMEZONE RESOLUTION
    # ==================================================

    @classmethod
    def timezone_name(
        cls,
        context=None,
    ) -> str:

        name = getattr(
            context,
            "timezone",
            None,
        )

        if not name:

            return cls.DEFAULT_TIMEZONE

        return str(name).strip()

    @classmethod
    def zone(
        cls,
        context=None,
    ) -> ZoneInfo:

        name = cls.timezone_name(
            context
        )

        try:

            return ZoneInfo(
                name
            )

        except (
            ZoneInfoNotFoundError,
            ValueError,
        ):

            logger.warning(
                "Unknown timezone %r; falling back to %s.",
                name,
                cls.DEFAULT_TIMEZONE,
            )

            return ZoneInfo(
                cls.DEFAULT_TIMEZONE
            )

    @classmethod
    def now(
        cls,
        context=None,
    ) -> datetime:

        return datetime.now(
            cls.zone(context)
        )

    @classmethod
    def today(
        cls,
        context=None,
    ) -> date:

        return cls.now(
            context
        ).date()

    # ==================================================
    # RELATIVE WINDOW RESOLUTION
    # ==================================================

    @staticmethod
    def _month_window(
        year: int,
        month: int,
    ) -> tuple[date, date]:

        last_day = calendar.monthrange(
            year,
            month,
        )[1]

        return (
            date(year, month, 1),
            date(year, month, last_day),
        )

    @staticmethod
    def _shift_month(
        anchor: date,
        months: int,
    ) -> tuple[int, int]:

        index = (
            anchor.year * 12
            + (anchor.month - 1)
            + months
        )

        return (
            index // 12,
            index % 12 + 1,
        )

    @classmethod
    def _week_window(
        cls,
        anchor: date,
        weeks: int,
    ) -> tuple[date, date]:

        monday = (
            anchor
            - timedelta(days=anchor.weekday())
            + timedelta(weeks=weeks)
        )

        return (
            monday,
            monday + timedelta(days=6),
        )

    @classmethod
    def resolve_relative_window(
        cls,
        text: str,
        *,
        today: date,
    ) -> tuple[date, date] | None:

        #
        # Deterministic resolution of the relative phrases a
        # follow-up actually uses. Returns None when the text
        # carries no relative window, so callers can fall back
        # to inherited or LLM-extracted dates.
        #
        # Ordering matters: the longer phrases must be tested
        # before the substrings they contain.
        #

        if not text:

            return None

        lowered = (
            text
            .lower()
            .strip()
        )

        # ----------------------------------------------
        # Single days
        # ----------------------------------------------

        if "day before yesterday" in lowered:

            target = today - timedelta(days=2)

            return (target, target)

        if "day after tomorrow" in lowered:

            target = today + timedelta(days=2)

            return (target, target)

        if "yesterday" in lowered:

            target = today - timedelta(days=1)

            return (target, target)

        if "tomorrow" in lowered:

            target = today + timedelta(days=1)

            return (target, target)

        if re.search(
            r"\btoday\b|\btonight\b",
            lowered,
        ):

            return (today, today)

        # ----------------------------------------------
        # Rolling day ranges ("last 7 days")
        # ----------------------------------------------

        rolling = re.search(
            r"\b(?:last|past|previous)\s+(\d{1,3})\s+days?\b",
            lowered,
        )

        if rolling:

            days = max(
                1,
                min(
                    int(rolling.group(1)),
                    366,
                ),
            )

            return (
                today - timedelta(days=days - 1),
                today,
            )

        # ----------------------------------------------
        # Weeks
        # ----------------------------------------------

        if re.search(
            r"\b(this|current)\s+week\b",
            lowered,
        ):

            return cls._week_window(today, 0)

        if re.search(
            r"\b(last|previous|past)\s+week\b",
            lowered,
        ):

            return cls._week_window(today, -1)

        if re.search(
            r"\b(next|coming|upcoming)\s+week\b",
            lowered,
        ):

            return cls._week_window(today, 1)

        # ----------------------------------------------
        # Months
        # ----------------------------------------------

        if re.search(
            r"\b(this|current)\s+month\b",
            lowered,
        ):

            return cls._month_window(
                today.year,
                today.month,
            )

        if re.search(
            r"\b(last|previous|past)\s+month\b",
            lowered,
        ):

            year, month = cls._shift_month(today, -1)

            return cls._month_window(year, month)

        if re.search(
            r"\b(next|coming|upcoming)\s+month\b",
            lowered,
        ):

            year, month = cls._shift_month(today, 1)

            return cls._month_window(year, month)

        # ----------------------------------------------
        # Years
        # ----------------------------------------------

        if re.search(
            r"\b(this|current)\s+year\b",
            lowered,
        ):

            return (
                date(today.year, 1, 1),
                date(today.year, 12, 31),
            )

        if re.search(
            r"\b(last|previous|past)\s+year\b",
            lowered,
        ):

            return (
                date(today.year - 1, 1, 1),
                date(today.year - 1, 12, 31),
            )

        if re.search(
            r"\b(next|coming|upcoming)\s+year\b",
            lowered,
        ):

            return (
                date(today.year + 1, 1, 1),
                date(today.year + 1, 12, 31),
            )

        return None

    @classmethod
    def has_relative_window(
        cls,
        text: str,
        *,
        today: date,
    ) -> bool:

        return (
            cls.resolve_relative_window(
                text,
                today=today,
            )
            is not None
        )
