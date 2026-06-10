class ActionExecutor:

    async def execute(
        self,
        action_type,
        payload,
        context
    ):

        if (
            action_type
            ==
            "create_personal_event"
        ):

            return await (
                self.create_personal_event(
                    payload,
                    context
                )
            )