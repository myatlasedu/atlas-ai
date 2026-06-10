
import json
import time
import requests
from datetime import datetime


API_URL = "http://127.0.0.1:8000/api/ai/query"

CONTEXT = {
    "user_id": 2,
    "role": "student",
    "campus_id": 1,
    "student_id": 1,
    "enrollment_id": 2,
    "academic_class_id": 1
}

QUERIES = [

    # =====================================================
    # PERFORMANCE
    # =====================================================

    "How am I doing overall?",
    "What are my strengths?",
    "What are my weaknesses?",
    "What should I focus on next?",
    "Am I improving?",
    "Am I getting better academically?",
    "How can I improve my Atlas score?",
    "Why is my performance declining?",
    "What concerns do you see?",
    "Am I at risk academically?",
    "Give me a complete performance review.",
    "Analyze my overall performance.",
    "What should I improve this week?",

    # =====================================================
    # ATLAS
    # =====================================================

    "What is my Atlas score?",
    "What Atlas band am I in?",
    "Which pillar is strongest?",
    "Which pillar is weakest?",
    "How is my academic pillar?",
    "How is my growth pillar?",
    "How is my initiative pillar?",
    "Explain my Atlas performance.",

    # =====================================================
    # ATTENDANCE
    # =====================================================

    "What is my attendance percentage?",
    "How is my attendance?",
    "Am I attending regularly?",
    "Do I have attendance issues?",
    "Show my attendance summary.",

    # =====================================================
    # HOMEWORK
    # =====================================================

    "Do I have pending homework?",
    "What homework is overdue?",
    "What homework is due today?",
    "What homework is due tomorrow?",
    "Show my homework summary.",
    "Any teacher feedback on homework?",

    # =====================================================
    # ASSESSMENTS
    # =====================================================

    "What is my latest assessment result?",
    "How are my assessments going?",
    "What is my highest scoring assessment?",
    "What is my lowest scoring assessment?",
    "Am I improving in assessments?",
    "Do I have pending assessments?",
    "Which assessments need attention?",
    "Show my assessment trend.",
    "Analyze my assessment performance.",

    # =====================================================
    # CROSS PLATFORM INTELLIGENCE
    # =====================================================

    "Why is my Atlas score low?",
    "Why is my growth score weak?",
    "What is causing my performance issues?",
    "What should I focus on to improve academically?",
    "What is affecting my Atlas score most?",
    "Are my homework and assessments aligned?",
    "Does attendance seem to be impacting my performance?",
    "What patterns do you see across my data?",
    "Summarize everything important about me.",
    "What should I prioritize first?",
    "Give me the top three areas to improve.",

    # =====================================================
    # REPORT
    # =====================================================

    "Generate my student report.",
    "Give me a full student report.",
    "Summarize my academic progress.",
    "Provide a complete overview of my performance.",

    # =====================================================
    # EVENTS
    # =====================================================

    "What events do I have tomorrow?",
    "Show my events for this week.",
    "Do I have any upcoming events?",
    "What personal reminders do I have?",
    "What study events are scheduled?",

    # =====================================================
    # EVENT CREATION
    # =====================================================

    "Remind me to study maths tomorrow at 6pm",
    "Schedule football practice on Saturday at 5pm",
    "Remind me about my chemistry exam next Monday",
    "Create a study session tomorrow from 7pm to 8pm",
    "Book a revision session on Friday at 4pm",

    # =====================================================
    # CONFIRMATION FLOW
    # =====================================================

    "yes",
    "confirm",
    "yes create it",
    "cancel",
    "no",

    # =====================================================
    # EDGE CASES
    # =====================================================

    "What should I do?",
    "How can I improve?",
    "Help me perform better.",
    "What needs attention?",
    "What should I focus on today?",
    "Give me recommendations.",
    "Analyze me.",
    "Review my progress.",
]

def call_api(query):

    payload = {
        "query": query,
        "context": CONTEXT
    }

    response = requests.post(
        API_URL,
        headers={
            "accept": "application/json",
            "Content-Type": "application/json"
        },
        json=payload,
        timeout=60
    )

    return {
        "status_code": response.status_code,
        "response": response.json()
    }


def main():

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    logfile = (
        f"atlas_score_test_log_{timestamp}.txt"
    )

    with open(
        logfile,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(
            "=" * 100 +
            "\ATLAS SCORE INTELLIGENCE TEST RUN\n" +
            "=" * 100 +
            "\n\n"
        )

        for index, query in enumerate(
            QUERIES,
            start=1
        ):

            print(
                f"[{index}/{len(QUERIES)}] {query}"
            )

            try:

                result = call_api(query)

                f.write(
                    "\n" +
                    "=" * 100 +
                    "\n"
                )

                f.write(
                    f"QUERY #{index}\n"
                )

                f.write(
                    f"QUESTION: {query}\n\n"
                )

                f.write(
                    f"STATUS: "
                    f"{result['status_code']}\n\n"
                )

                f.write(
                    json.dumps(
                        result["response"],
                        indent=2,
                        ensure_ascii=False
                    )
                )

                f.write("\n")

            except Exception as e:

                f.write(
                    "\n" +
                    "=" * 100 +
                    "\n"
                )

                f.write(
                    f"QUERY #{index}\n"
                )

                f.write(
                    f"QUESTION: {query}\n\n"
                )

                f.write(
                    f"ERROR: {str(e)}\n"
                )

            time.sleep(0.5)

    print(
        f"\nFinished.\n"
        f"Log saved to: {logfile}"
    )


if __name__ == "__main__":
    main()