class ScreenNavigationTool:

    async def run(
        self,
        context,
        parsed_intent
    ):

        navigation_target = (
            parsed_intent.navigation_target
        )

        return {

            "module":
                "navigation",

            "navigate":
                navigation_target is not None,

            "navigation_target":
                navigation_target
        }