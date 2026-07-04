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
        parsed_intent
    ):

        if not context.academic_class_id:

            return {
                "error":
                "Academic class missing"
            }

        query = (
            getattr(
                parsed_intent,
                "original_query",
                ""
            )
            .lower()
            .replace("?", "")
            .replace(".", "")
            .replace("!", "")
            .strip()
        )

        async with AsyncSessionLocal() as db:

            repo = AnnouncementRepository(
                db
            )

            announcements = (
                await repo.get_recent_announcements(
                    context.academic_class_id
                )
            )

            latest = (
                await repo.get_latest_announcement(
                    context.academic_class_id
                )
            )

            payload = {

                "module":
                    "announcement",

                "announcement_count":
                    len(announcements),

                "latest_announcement":
                    latest,

                "latest_title":
                    (
                        latest["title"]
                        if latest
                        else None
                    ),

                "latest_created_at":
                    (
                        latest["created_at"]
                        if latest
                        else None
                    ),

                "recent_announcements":
                    announcements
            }

            # =====================================
            # SUMMARY / OVERVIEW
            # =====================================

            if any(
                phrase in query
                for phrase in [
                    "summary",
                    "overview",
                    "recent announcements",
                    "recent updates",
                    "announcement summary",
                    "announcement overview",
                    "school updates",
                    "show all announcements"
                ]
            ):

                if announcements:

                    titles = [
                        item["title"]
                        for item in announcements[:5]
                    ]

                    payload[
                        "direct_answer"
                    ] = (
                        f"There are "
                        f"{len(announcements)} "
                        f"recent announcement(s): "
                        f"{', '.join(titles)}."
                    )

                else:

                    payload[
                        "direct_answer"
                    ] = (
                        "There are currently "
                        "no announcements."
                    )

                return payload

            # =====================================
            # LATEST ANNOUNCEMENT
            # =====================================

            if any(
                phrase in query
                for phrase in [
                    "announcement",
                    "announcements",
                    "notice",
                    "notices",
                    "latest update",
                    "latest announcement",
                    "latest notice",
                    "whats new",
                    "what's new",
                    "new update",
                    "new updates",
                    "school update",
                    "class announcement",
                    "class announcements"
                ]
            ):

                if latest:

                    payload[
                        "direct_answer"
                    ] = (
                        f"Latest announcement: "
                        f"{latest['title']}."
                    )

                else:

                    payload[
                        "direct_answer"
                    ] = (
                        "There are currently "
                        "no announcements."
                    )

                return payload

            return payload