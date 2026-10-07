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

            is_guardian = (
                getattr(context, "role", None)
                == "guardian"
            )

            if forums:

                membership_answer = (
                    (
                        "Your child is a member of "
                        if is_guardian
                        else "You are a member of "
                    )
                    + f"{len(forums)} forum(s): "
                    + ", ".join(
                        forum["title"]
                        for forum in forums
                    )
                    + "."
                )

            else:

                membership_answer = (
                    "Your child is not a member of any forums."
                    if is_guardian
                    else "You are not a member of any forums."
                )

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

                payload[
                    "direct_answer"
                ] = membership_answer

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

            # =====================================
            # GENERAL FORUM QUESTION
            # =====================================

            payload["direct_answer"] = membership_answer

            if latest_announcement:

                payload["direct_answer"] += (
                    " Latest forum announcement from "
                    f"{latest_announcement['forum_title']}: "
                    f"{latest_announcement['message']}"
                )

            return payload