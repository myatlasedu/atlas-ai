from db.session import (
    AsyncSessionLocal
)

from db.repositories.student.announcement_repository import (
    AnnouncementRepository
)


class AnnouncementTool:

    async def run(
        self,
        context,
        parsed_intent,
    ):

        if not context.academic_class_id:

            return {

                "module":
                    "announcement",

                "announcement_count":
                    0,

                "announcements":
                    [],

                "direct_answer":
                    "Academic class information is unavailable."
            }

        query = (
            getattr(
                parsed_intent,
                "original_query",
                "",
            )
            .lower()
        )

        keyword = getattr(
            parsed_intent,
            "topic",
            None,
        )

        start_date = getattr(
            parsed_intent,
            "start_date",
            None,
        )

        end_date = getattr(
            parsed_intent,
            "end_date",
            None,
        )

        async with AsyncSessionLocal() as db:

            repo = AnnouncementRepository(
                db
            )

            #
            # Latest announcement
            #

            if any(
                phrase in query
                for phrase in [
                    "latest",
                    "recent",
                    "newest",
                    "last announcement",
                ]
            ):

                latest = await repo.get_latest_announcement(
                    context.academic_class_id
                )

                if latest:

                    return {

                        "module":
                            "announcement",

                        "announcement_count":
                            1,

                        "announcements":
                            [latest],

                        "llm_context": {

                            "announcement_count": 1,

                            "latest_announcement":
                                latest,
                        },

                        "direct_answer":
                            (
                                f"Latest announcement: "
                                f"{latest['title']}"
                            ),
                    }

                return {

                    "module":
                        "announcement",

                    "announcement_count":
                        0,

                    "announcements":
                        [],

                    "llm_context": {

                        "announcement_count": 0,
                    },

                    "direct_answer":
                        "There are currently no announcements.",
                }

            #
            # Oldest announcement
            #

            if any(
                phrase in query
                for phrase in [
                    "first announcement",
                    "oldest announcement",
                    "earliest announcement",
                ]
            ):

                oldest = await repo.get_oldest_announcement(
                    context.academic_class_id
                )

                if oldest:

                    return {

                        "module":
                            "announcement",

                        "announcement_count":
                            1,

                        "announcements":
                            [oldest],

                        "llm_context": {

                            "announcement_count": 1,

                            "latest_announcement":
                                oldest,
                        },

                        "direct_answer":
                            (
                                f"First announcement: "
                                f"{oldest['title']}"
                            ),
                    }

                return {

                    "module":
                        "announcement",

                    "announcement_count":
                        0,

                    "announcements":
                        [],

                    "llm_context": {

                        "announcement_count": 0,
                    },

                    "direct_answer":
                        "There are currently no announcements.",
                }

            #
            # General search
            #

            announcements = await repo.search_announcements(

                academic_class_id=context.academic_class_id,

                start_date=start_date,

                end_date=end_date,

                keyword=keyword,
            )

            payload = {

                "module":
                    "announcement",

                "announcement_count":
                    len(
                        announcements
                    ),

                "announcements":
                    announcements,

                "llm_context": {

                    "announcement_count":
                        len(
                            announcements
                        ),

                    "latest_announcement":
                        announcements[0]
                        if announcements
                        else None,

                    "announcements":
                        announcements,
                },
            }

            if announcements:

                lines = [

                    f"Found {len(announcements)} announcement{'s' if len(announcements) != 1 else ''}.",
                    "",
                ]

                for item in announcements:

                    lines.append(

                        f"• [{item['created_at']}] "
                        f"{item['title']}"
                    )

                payload["direct_answer"] = "\n".join(
                    lines
                )

            else:

                if keyword:

                    payload["direct_answer"] = (
                        f"No announcements were found matching '{keyword}'."
                    )

                elif start_date or end_date:

                    payload["direct_answer"] = (
                        "No announcements were found in that date range."
                    )

                else:

                    payload["direct_answer"] = (
                        "There are currently no announcements."
                    )

            return payload