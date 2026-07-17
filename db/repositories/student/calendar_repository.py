from sqlalchemy import text


class CalendarRepository:

    EVENT_TYPE_MAP = {
        1: "Holiday",
        2: "Exam",
        3: "Activity",
        4: "Event",
    }

    EVENT_TYPE_FILTERS = {

        "holiday": 1,
        "holidays": 1,

        "exam": 2,
        "exams": 2,

        "activity": 3,
        "activities": 3,

        "event": 4,
        "events": 4,
    }

    def __init__(
        self,
        db,
    ):
        self.db = db

    async def search_events(
        self,
        academic_class_id: int,
        start_date=None,
        end_date=None,
        keyword=None,
        limit: int = 20,
    ):

        where = [

            "ecm.academic_class_id = :academic_class_id",
        ]

        params = {

            "academic_class_id": academic_class_id,

            "limit": limit,
        }

        #
        # Date filters
        #

        if start_date:

            where.append(
                "DATE(e.start_datetime) >= :start_date"
            )

            params["start_date"] = start_date

        if end_date:

            where.append(
                "DATE(e.start_datetime) <= :end_date"
            )

            params["end_date"] = end_date

        #
        # Event type filter
        #

        event_type = None

        if keyword:

            event_type = self.EVENT_TYPE_FILTERS.get(
                keyword.lower()
            )

        if event_type:

            where.append(
                "e.event_type = :event_type"
            )

            params["event_type"] = event_type

        #
        # Generic keyword search
        #

        elif keyword:

            where.append(
                """
                (
                    LOWER(e.title) LIKE LOWER(:keyword)
                    OR
                    LOWER(COALESCE(e.description,'')) LIKE LOWER(:keyword)
                )
                """
            )

            params["keyword"] = f"%{keyword}%"

        query = text(
            f"""
            SELECT

                e.id,

                e.title,

                e.description,

                e.event_type,

                e.start_datetime,

                e.end_datetime,

                e.is_all_day

            FROM schools_schoolevent e

            INNER JOIN schools_schooleventclassmap ecm

                ON ecm.school_event_id = e.id

            WHERE

                {" AND ".join(where)}

            ORDER BY

                e.start_datetime ASC

            LIMIT :limit
            """
        )

        result = await self.db.execute(
            query,
            params,
        )

        events = []

        for row in result.mappings():

            item = dict(row)

            item["event_type"] = self.EVENT_TYPE_MAP.get(
                item["event_type"],
                "Unknown",
            )

            events.append(item)

        return events

    async def get_latest_event(
        self,
        academic_class_id: int,
    ):

        query = text(
            """
            SELECT

                e.id,
                e.title,
                e.description,
                e.event_type,
                e.start_datetime,
                e.end_datetime,
                e.is_all_day

            FROM schools_schoolevent e

            INNER JOIN schools_schooleventclassmap ecm

                ON ecm.school_event_id = e.id

            WHERE

                ecm.academic_class_id = :academic_class_id

            ORDER BY

                e.created_at DESC

            LIMIT 1
            """
        )

        result = await self.db.execute(
            query,
            {
                "academic_class_id": academic_class_id,
            },
        )

        row = result.mappings().first()

        if not row:

            return None

        item = dict(row)

        item["event_type"] = self.EVENT_TYPE_MAP.get(
            item["event_type"],
            "Unknown",
        )

        return item

    async def get_oldest_event(
        self,
        academic_class_id: int,
    ):

        query = text(
            """
            SELECT

                e.id,
                e.title,
                e.description,
                e.event_type,
                e.start_datetime,
                e.end_datetime,
                e.is_all_day

            FROM schools_schoolevent e

            INNER JOIN schools_schooleventclassmap ecm

                ON ecm.school_event_id = e.id

            WHERE

                ecm.academic_class_id = :academic_class_id

            ORDER BY

                e.start_datetime ASC

            LIMIT 1
            """
        )

        result = await self.db.execute(
            query,
            {
                "academic_class_id": academic_class_id,
            },
        )

        row = result.mappings().first()

        if not row:

            return None

        item = dict(row)

        item["event_type"] = self.EVENT_TYPE_MAP.get(
            item["event_type"],
            "Unknown",
        )

        return item

    async def get_upcoming_events(
        self,
        academic_class_id: int,
        limit: int = 5,
    ):

        query = text(
            """
            SELECT

                e.id,
                e.title,
                e.description,
                e.event_type,
                e.start_datetime,
                e.end_datetime,
                e.is_all_day

            FROM schools_schoolevent e

            INNER JOIN schools_schooleventclassmap ecm

                ON ecm.school_event_id = e.id

            WHERE

                ecm.academic_class_id = :academic_class_id

                AND DATE(e.start_datetime) >= CURRENT_DATE

            ORDER BY

                e.start_datetime ASC

            LIMIT :limit
            """
        )

        result = await self.db.execute(
            query,
            {
                "academic_class_id": academic_class_id,
                "limit": limit,
            },
        )

        events = []

        for row in result.mappings():

            item = dict(row)

            item["event_type"] = self.EVENT_TYPE_MAP.get(
                item["event_type"],
                "Unknown",
            )

            events.append(item)

        return events