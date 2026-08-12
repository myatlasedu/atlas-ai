from db.session import (
    AsyncSessionLocal,
)

from db.repositories.student.resource_repository import (
    ResourceRepository,
)


class ResourceTool:

    async def run(
        self,
        context,
        parsed_intent,
    ):

        if not context.enrollment_id:

            return {
                "module":
                    "resource",
                "error":
                    "Enrollment ID missing",
                "direct_answer":
                    "Unable to load resource information.",
            }

        subject = getattr(
            parsed_intent,
            "subject",
            None,
        )

        topic = getattr(
            parsed_intent,
            "topic",
            None,
        )

        async with AsyncSessionLocal() as db:

            repo = ResourceRepository(
                db
            )

            resources = (
                await repo.get_resources(
                    context.enrollment_id,
                    subject=subject,
                    topic=topic,
                )
            )

        resource_count = len(resources)

        resource_items = [
            {
                "name": row.get(
                    "name",
                    "Resource",
                ),
                "subject_name": row.get(
                    "subject_name",
                    None,
                ),
                "topic_name": row.get(
                    "topic_name",
                    None,
                ),
                "media_type": row.get(
                    "media_type",
                    None,
                ),
                "file": row.get(
                    "file",
                    None,
                ),
                "external_url": row.get(
                    "external_url",
                    None,
                ),
            }
            for row in resources[:20]
        ]

        payload = {
            "module":
                "resource",
            "subject":
                subject,
            "topic":
                topic,
            "resource_count":
                resource_count,
            "resources":
                resource_items,
            "llm_context": {
                "status":
                    "available"
                    if resource_count
                    else "none",
                "metrics": {
                    "resource_count": resource_count,
                },
                "subject":
                    subject,
                "topic":
                    topic,
                "highlights": [
                    (
                        f"{resource_count} resource(s) found."
                        if resource_count
                        else "No resources found."
                    ),
                ],
                "resource_items":
                    resource_items,
            },
        }

        if not resource_count:

            payload["direct_answer"] = (
                "There are currently no supplementary sheets "
                "or resources available"
                + (
                    f" for {subject}."
                    if subject
                    else "."
                )
            )

        return payload
