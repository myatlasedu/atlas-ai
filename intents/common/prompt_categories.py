import random


STUDENT_PROMPT_CATEGORIES = {

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


GUARDIAN_PROMPT_CATEGORIES = {

    "Atlas Score": [
        "Show my child's Atlas score.",
        "How can my child improve their Atlas score?",
        "Which Atlas pillar needs the most improvement for my child?",
    ],

    "Performance": [
        "How is my child doing overall?",
        "Which subject needs the most attention for my child?",
        "Compare my child's subjects.",
    ],

    "Topics": [
        "Show my child's completed topics.",
        "Which topics are still pending for my child?",
        "Which topics is my child weak in?",
    ],

    "Homework": [
        "What homework is due today for my child?",
        "Show my child's homework this week.",
        "Does my child have any overdue homework?",
    ],

    "Assessments": [
        "Show my child's upcoming assessments.",
        "How did my child perform in recent assessments?",
        "Which assessment affected my child's performance the most?",
    ],

    "Attendance": [
        "Show my child's attendance this month.",
        "How consistent has my child's attendance been?",
    ],

    "Structure of the Day": [
        "Show my child's Structure of the Day today.",
        "What's my child's Structure of the Day tomorrow?",
        "What lesson does my child have next?",
    ],

    "Calendar": [
        "Show my child's upcoming school events.",
        "What school events does my child have this week?",
        "Does my child have any school events tomorrow?",
    ],

    "Announcements": [
        "Show recent announcements for my child's school.",
    ],
}


def build_unknown_intent_summary(
    audience: str,
):

    prompt_categories = (
        STUDENT_PROMPT_CATEGORIES
        if audience == "student"
        else GUARDIAN_PROMPT_CATEGORIES
    )

    summary = (
        "I'm not quite sure what you're looking for.\n\n"
        "Atlas can help with many aspects of your academic journey. "
        "Here are a few things you can try:\n\n"
    )

    for category, prompts in prompt_categories.items():

        summary += (
            f"{category}\n"
            f"• {random.choice(prompts)}\n\n"
        )

    summary += (
        "You don't need to use these exact phrases—you can ask naturally, "
        "and I'll do my best to understand."
    )

    return summary