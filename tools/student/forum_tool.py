from db.session import (
    AsyncSessionLocal
)

from db.repositories.student.forum_repository import (
    ForumRepository
)


class ForumTool:

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

            repo = ForumRepository(
                db
            )

            forums = (
                await repo.get_my_forums(
                    context.enrollment_id
                )
            )

            latest_announcement = (
                await repo.get_latest_forum_announcement(
                    context.enrollment_id
                )
            )

            announcements = (
                await repo.get_recent_forum_announcements(
                    context.enrollment_id
                )
            )

            payload = {

                "module":
                    "forum",

                "forum_count":
                    len(forums),

                "forums":
                    forums,

                "latest_announcement":
                    latest_announcement,

                "recent_announcements":
                    announcements
            }

            # =====================================
            # MEMBERSHIPS / CLUBS
            # =====================================

            if any(
                phrase in query
                for phrase in [
                    "my forums",
                    "joined forums",
                    "forum memberships",
                    "which forums",
                    "show my forums",
                    "my clubs",
                    "clubs",
                    "club memberships",
                    "show my clubs",
                    "joined clubs",
                    "what clubs am i part of",
                    "community memberships",
                    "communities"
                ]
            ):

                if forums:

                    titles = [
                        forum["title"]
                        for forum in forums
                    ]

                    payload[
                        "direct_answer"
                    ] = (
                        f"You are a member of "
                        f"{len(forums)} forum(s): "
                        f"{', '.join(titles)}."
                    )

                else:

                    payload[
                        "direct_answer"
                    ] = (
                        "You are not a member "
                        "of any forums."
                    )

                return payload

            # =====================================
            # FORUM ANNOUNCEMENTS
            # =====================================

            if any(
                phrase in query
                for phrase in [
                    "forum announcement",
                    "forum announcements",
                    "forum update",
                    "forum updates",
                    "forum notice",
                    "forum notices",
                    "latest forum announcement",
                    "recent forum announcements",
                    "club announcement",
                    "club announcements",
                    "club updates",
                    "community announcement",
                    "community announcements"
                ]
            ):

                if announcements:

                    if len(announcements) == 1:

                        latest = announcements[0]

                        payload[
                            "direct_answer"
                        ] = (
                            f"Latest forum announcement "
                            f"from "
                            f"{latest['forum_title']}: "
                            f"{latest['message']}"
                        )

                    else:

                        forum_names = list(
                            {
                                item["forum_title"]
                                for item in announcements
                            }
                        )

                        payload[
                            "direct_answer"
                        ] = (
                            f"There are "
                            f"{len(announcements)} "
                            f"recent forum announcement(s) "
                            f"across "
                            f"{', '.join(forum_names)}."
                        )

                else:

                    payload[
                        "direct_answer"
                    ] = (
                        "No forum announcements "
                        "are currently available."
                    )

                return payload

            return payload