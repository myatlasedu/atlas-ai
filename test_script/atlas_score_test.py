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
    "How is my engagement pillar?",
    "Explain my Atlas performance.",
    "Why is my Atlas score low?",
    "Why is my growth score weak?",
    "What is affecting my Atlas score most?",

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
    # CROSS MODULE
    # =====================================================

    "What is causing my performance issues?",
    "What should I focus on to improve academically?",
    "Are my homework and assessments aligned?",
    "Does attendance seem to be impacting my performance?",
    "What patterns do you see across my data?",
    "Summarize everything important about me.",
    "What should I prioritize first?",
    "Give me the top three areas to improve."
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

    try:

        body = response.json()

    except Exception:

        body = response.text

    return {

        "status_code": response.status_code,

        "response": body
    }


def main():

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    logfile = (
        f"atlas_regression_{timestamp}.txt"
    )

    total = 0

    passed = 0

    failed = 0

    total_time = 0

    with open(
        logfile,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(
            "=" * 120 + "\n"
        )

        f.write(
            "ATLAS AI REGRESSION TEST\n"
        )

        f.write(
            "=" * 120 + "\n\n"
        )

        for index, query in enumerate(
            QUERIES,
            start=1
        ):

            print(
                f"[{index}/{len(QUERIES)}] {query}"
            )

            total += 1

            start = time.perf_counter()

            try:

                result = call_api(
                    query
                )

                elapsed = round(
                    time.perf_counter() - start,
                    3
                )

                total_time += elapsed

                ok = (
                    result["status_code"]
                    == 200
                )

                if ok:

                    passed += 1

                else:

                    failed += 1

                f.write(
                    "=" * 120 + "\n"
                )

                f.write(
                    f"QUERY #{index}\n\n"
                )

                f.write(
                    f"QUESTION : {query}\n"
                )

                f.write(
                    f"STATUS   : {result['status_code']}\n"
                )

                f.write(
                    f"TIME     : {elapsed:.3f}s\n"
                )

                f.write(
                    f"PASS     : {ok}\n\n"
                )

                if isinstance(
                    result["response"],
                    dict
                ):

                    f.write(
                        json.dumps(
                            result["response"],
                            indent=2,
                            ensure_ascii=False
                        )
                    )

                else:

                    f.write(
                        str(
                            result["response"]
                        )
                    )

                f.write("\n\n")

            except Exception as e:

                elapsed = round(
                    time.perf_counter() - start,
                    3
                )

                failed += 1

                total_time += elapsed

                f.write(
                    "=" * 120 + "\n"
                )

                f.write(
                    f"QUERY #{index}\n\n"
                )

                f.write(
                    f"QUESTION : {query}\n"
                )

                f.write(
                    f"TIME     : {elapsed:.3f}s\n"
                )

                f.write(
                    "PASS     : False\n\n"
                )

                f.write(
                    f"ERROR: {str(e)}\n\n"
                )

            time.sleep(0.5)

        average = round(
            total_time / total,
            3
        )

        f.write(
            "=" * 120 + "\n"
        )

        f.write(
            "SUMMARY\n"
        )

        f.write(
            "=" * 120 + "\n\n"
        )

        f.write(
            f"Total Queries : {total}\n"
        )

        f.write(
            f"Passed        : {passed}\n"
        )

        f.write(
            f"Failed        : {failed}\n"
        )

        f.write(
            f"Average Time  : {average}s\n"
        )

        f.write(
            f"Total Time    : {round(total_time, 2)}s\n"
        )

    print()

    print("=" * 80)

    print("Regression Complete")

    print(f"Total   : {total}")

    print(f"Passed  : {passed}")

    print(f"Failed  : {failed}")

    print(f"Average : {average}s")

    print(f"Log File : {logfile}")

    print("=" * 80)


if __name__ == "__main__":

    main()