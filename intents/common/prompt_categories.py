import random


PROMPT_CATEGORIES = {

    "Atlas Score": [

        "Show my Atlas score.",
        "How can I improve my Atlas score?",
        "Which Atlas pillar needs the most improvement?",
    ],

    "Performance": [

        "How am I doing overall?",
        "Which subject needs the most attention?",
        "Compare my subjects.",
    ],

    "Topics": [

        "Show completed topics.",
        "Which topics are still pending?",
        "Which topics am I weak in?",
    ],

    "Homework": [

        "What homework is due today?",
        "Show my homework this week.",
        "Do I have any overdue homework?",
    ],

    "Assessments": [

        "Show my upcoming assessments.",
        "How did I perform in my recent assessments?",
        "Which assessment affected my performance the most?",
    ],

    "Attendance": [

        "Show my attendance this month.",
        "How consistent has my attendance been?",
    ],

    "Structure of the Day": [

        "Show today's Structure of the Day.",
        "What's my Structure of the Day tomorrow?",
        "What lesson do I have next?",
    ],

    "Calendar": [

        "Show upcoming school events.",
        "What events are happening this week?",
        "Do I have any school events tomorrow?",
    ],

    "Announcements": [

        "Show recent announcements.",
    ],

    "Journal": [

        "Show my journal.",
        "Show my journal from last week.",
        "Save this in my journal: Today I finally understood quadratic equations.",
        "Journal this: Today was a productive day.",
        "Today I learned how to solve simultaneous equations. Save this in my journal.",
        "Journal my goal to complete homework before dinner every day.",
    ],
}


def build_unknown_intent_summary():

    examples = []

    for category, prompts in PROMPT_CATEGORIES.items():

        examples.append(
            (
                category,
                random.choice(prompts),
            )
        )

    summary = (
        "I'm not quite sure what you're looking for.\n\n"
        "Atlas can help with many aspects of your academic journey. "
        "Here are a few things you can try:\n\n"
    )

    for category, prompt in examples:

        summary += (
            f"{category}\n"
            f"• {prompt}\n\n"
        )

    summary += (
        "You don't need to use these exact phrases—"
        "you can ask naturally, and I'll do my best to understand."
    )

    return summary