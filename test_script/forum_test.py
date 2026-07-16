
import json
import time
import requests
from datetime import datetime
from utils import ist_now


API_URL = "http://127.0.0.1:8000/api/ai/query"

CONTEXT = {
    "user_id": 2,
    "role": "student",
    "campus_id": 1,
    "student_id": 2,
    "enrollment_id": 4,
    "academic_class_id": 2
}

QUERIES = [

    "My forums",

    "Which forums am I a member of?",

    "Show my joined forums",

    "Forum announcements",

    "Any forum updates?",

    "Latest forum announcement",

    "Forum notices",

    "Show forum memberships",

    "What clubs am I part of?",

    "Recent forum announcements"
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

    timestamp = ist_now().strftime(
        "%Y%m%d_%H%M%S"
    )

    logfile = (
        f"forum_test_log_{timestamp}.txt"
    )

    with open(
        logfile,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(
            "=" * 100 +
            "\FORUM INTELLIGENCE TEST RUN\n" +
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