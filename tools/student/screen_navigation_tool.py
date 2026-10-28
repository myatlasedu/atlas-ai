class ScreenNavigationTool:

    async def run(
        self,
        context,
        parsed_intent
    ):

        return {

            "module":
                "navigation",

            "navigate":
                True,

            "navigation_target":
                parsed_intent.navigation_target
        }