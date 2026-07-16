import json
import time
from datetime import datetime
from utils import ist_now
import requests
from utils import ist_now

API_URL = "http://127.0.0.1:8000/api/ai/query"

CONTEXT = {
    "user_id": 14,
    "role": "student",
    "campus_id": 1,
    "student_id": 11,
    "enrollment_id": 13,
    "academic_class_id": 4
}


TEST_SUITES = {

    "Attendance": [

        "Show my attendance.",
        "What is my attendance percentage?",
        "How many days was I absent?",
        "Was I late this month?",
        "Show my attendance trend.",
        "How is my attendance this term?",
        "Do I have low attendance?",
        "How many classes have I attended?"
    ],

    "Homework": [

        "Show my homework.",
        "What homework is pending?",
        "Any overdue homework?",
        "What homework is due today?",
        "What homework is due tomorrow?",
        "Show homework feedback.",
        "Which homework has been graded?",
        "Show my latest homework."
    ],

    "Assessment": [

        "Show my assessments.",
        "Show my latest test.",
        "What marks did I score?",
        "How did I perform in my last exam?",
        "Show assessment feedback.",
        "Which assessments are pending?",
        "What is my average score?",
        "Show my assessment summary."
    ],

    "Performance": [

        "How am I doing overall?",
        "What are my strengths?",
        "What are my weaknesses?",
        "Am I improving academically?",
        "How is my academic progress?",
        "What should I focus on next?",
        "How can I improve?",
        "What concerns do you see?"
    ],

    "Atlas Score": [

        "Show my Atlas score.",
        "How is my Atlas score calculated?",
        "Why did my Atlas score decrease?",
        "How can I improve my Atlas score?",
        "What affects my Atlas score?"
    ],

    "Subjects": [

        "Show my subjects.",
        "How am I doing in Maths?",
        "How am I doing in English?",
        "Which subject is my strongest?",
        "Which subject needs improvement?",
        "Show subject performance.",
        "Show Science progress."
    ],

    "Topics": [

        "Show completed topics.",
        "Which topics are pending?",
        "Which topics am I weak in?",
        "Show topic progress.",
        "Which chapter should I revise next?"
    ],

    "Announcements": [

        "Show announcements.",
        "Any new notices?",
        "What's new today?",
        "Show school announcements.",
        "Any important updates?"
    ],

    "Forum": [

        "Open forum.",
        "Show recent discussions.",
        "Show forum posts.",
        "Any unanswered questions?",
        "Latest community discussions."
    ],

    "Journal": [

        "Show my journal.",
        "Show my latest journal entry.",
        "Create a journal entry.",
        "Add a journal entry for today.",
        "Write a reflection about today's classes."
    ],

    "Calendar": [

        "Show my calendar.",
        "What events are coming up?",
        "Create a reminder for tomorrow.",
        "Add an event this Friday.",
        "Show my reminders."
    ],

    "Navigation": [

        "Open homework.",
        "Open attendance.",
        "Go to assessments.",
        "Open profile.",
        "Take me to dashboard."
    ]
}


def call_api(
    query
):

    payload = {

        "query":
            query,

        "context":
            CONTEXT
    }

    response = requests.post(

        API_URL,

        headers={

            "accept":
                "application/json",

            "Content-Type":
                "application/json"
        },

        json=payload,

        timeout=120
    )

    try:

        body = response.json()

    except Exception:

        body = response.text

    return response.status_code, body


def separator(
    file,
    char="="
):

    file.write(
        char * 120
        + "\n"
    )


def main():

    timestamp = (
        ist_now()
        .strftime("%Y%m%d_%H%M%S")
    )

    logfile = (
        f"student_ai_test_{timestamp}.txt"
    )

    total = (
        sum(
            len(x)
            for x in TEST_SUITES.values()
        )
    )

    completed = 0

    start_suite = time.perf_counter()

    with open(

        logfile,

        "w",

        encoding="utf-8"

    ) as f:

        separator(f)

        f.write(
            "ATLAS AI STUDENT REGRESSION TEST\n"
        )

        separator(f)

        f.write(
            f"\nStarted : {ist_now()}\n"
        )

        f.write(
            f"API     : {API_URL}\n"
        )

        f.write(
            f"Queries : {total}\n\n"
        )

        for category, queries in TEST_SUITES.items():

            separator(f)

            f.write(
                f"{category.upper()}\n"
            )

            separator(f)

            f.write("\n")

            for query in queries:

                completed += 1

                print(
                    f"[{completed}/{total}] {query}"
                )

                started = (
                    time.perf_counter()
                )

                try:

                    status, body = (
                        call_api(query)
                    )

                    elapsed = (
                        time.perf_counter()
                        -
                        started
                    ) * 1000

                    intent = None
                    view = None
                    modules = None

                    if isinstance(
                        body,
                        dict
                    ):

                        parsed = body.get(
                            "intent",
                            {}
                        )

                        intent = parsed.get(
                            "intent"
                        )

                        view = parsed.get(
                            "view"
                        )

                        modules = parsed.get(
                            "target_modules"
                        )

                    f.write(
                        "-" * 120 + "\n"
                    )

                    f.write(
                        f"Query      : {query}\n"
                    )

                    f.write(
                        f"Status     : {status}\n"
                    )

                    f.write(
                        f"Time       : {elapsed:.2f} ms\n"
                    )

                    f.write(
                        f"Intent     : {intent}\n"
                    )

                    f.write(
                        f"View       : {view}\n"
                    )

                    f.write(
                        f"Modules    : {modules}\n\n"
                    )

                    if isinstance(
                        body,
                        dict
                    ):

                        f.write(
                            json.dumps(
                                body,
                                indent=2,
                                ensure_ascii=False
                            )
                        )

                    else:

                        f.write(
                            str(body)
                        )

                    f.write("\n\n")

                except Exception as e:

                    elapsed = (
                        time.perf_counter()
                        -
                        started
                    ) * 1000

                    f.write(
                        "-" * 120 + "\n"
                    )

                    f.write(
                        f"Query      : {query}\n"
                    )

                    f.write(
                        f"FAILED\n"
                    )

                    f.write(
                        f"Time       : {elapsed:.2f} ms\n"
                    )

                    f.write(
                        f"Error      : {e}\n\n"
                    )

                time.sleep(0.25)

        separator(f)

        total_time = (
            time.perf_counter()
            -
            start_suite
        )

        f.write(
            f"\nCompleted in {total_time:.2f} seconds\n"
        )

        separator(f)

    print()
    print("=" * 80)
    print("Finished successfully.")
    print(f"Log written to: {logfile}")
    print("=" * 80)


if __name__ == "__main__":

    main()