RESPONSE_FORMAT = """
==================================================
RESPONSE FORMAT
==================================================

Example:

{
    "intent": "homework_summary",

    "navigation_target": null,

    "start_date": null,

    "end_date": null,

    "target_modules": [
        "homework"
    ],

    "confidence": 0.95
}

Navigation Example:

{
    "intent": "screen_navigation",

    "navigation_target": "homework",

    "start_date": null,

    "end_date": null,

    "target_modules": [],

    "confidence": 0.99
}

Return JSON only.
"""