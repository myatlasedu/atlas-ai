
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

    # =====================================
    # TREND DETECTION
    # =====================================

    "Are my scores improving?",
    "Am I getting better in assessments?",
    "Assessment trend",
    "Score trend",
    "Performance trend",
    "How are my recent assessment results compared to earlier ones?",
    "Is my assessment performance improving?",
    "Am I improving in assessments?",
    "Has my assessment performance improved over time?",
    "How have my scores changed over time?",

    # =====================================
    # TREND ANALYSIS
    # =====================================

    "Analyze my assessment trend.",
    "Analyse my assessment trend.",
    "What does my assessment trend indicate?",
    "Why are my grades dropping?",
    "Why is my performance declining?",
    "What concerns do you see in my assessment performance?",
    "Review my assessment trend.",
    "Explain my assessment trend.",
    "What patterns do you see in my assessment results?",
    "How should I interpret my assessment trend?",

    # =====================================
    # CONSISTENCY
    # =====================================

    "How consistent are my scores?",
    "Am I consistent in assessments?",
    "Assessment consistency",
    "Score consistency",
    "Are my assessment scores stable?",
    "Do I perform consistently in assessments?",
    "How variable are my assessment scores?",
    "How stable is my assessment performance?",
    "Is my performance consistent across assessments?",
    "Do my scores fluctuate a lot?",

    # =====================================
    # IMPROVEMENT
    # =====================================

    "What should I improve in assessments?",
    "How can I improve my assessment performance?",
    "What assessment should I focus on next?",
    "What is holding back my assessment performance?",
    "Which assessment needs attention?",
    "What should I work on before my next assessment?",
    "How can I raise my average score?",
    "What are my assessment weaknesses?",
    "What should I improve based on my assessment history?",
    "What should I focus on to improve my results?",

    # =====================================
    # PERFORMANCE SUMMARY
    # =====================================

    "How am I performing in assessments?",
    "Assessment summary",
    "Assessment review",
    "Assessment analysis",
    "How am I doing in assessments?",
    "Analyze my assessments.",
    "Analyze my performance.",
    "Give me an assessment performance summary.",
    "Review my assessment performance.",
    "How strong is my assessment performance?",

    # =====================================
    # HALLUCINATION TESTS
    # =====================================

    "Analyze my assessment trend only.",
    "Use only assessment data.",
    "Assessment analysis only.",
    "Do not use attendance.",
    "Do not use homework.",
    "Ignore Atlas score.",
    "Analyze only my assessment results.",
    "Explain my assessment performance without discussing attendance.",
    "Review my assessments only.",
    "Assessment insights only.",

    # =====================================
    # EDGE CASES
    # =====================================

    "Why am I not improving?",
    "What is my biggest assessment risk?",
    "What concerns do you see?",
    "What should be my next academic focus?",
    "What assessment is affecting my average the most?",
    "What is causing weaker assessment performance?",
    "What should I do before upcoming assessments?",
    "How prepared am I for future assessments?",
    "What does my recent performance suggest?",
    "What are the main insights from my assessments?"
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
        f"assessment_trend_test_log_{timestamp}.txt"
    )

    with open(
        logfile,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(
            "=" * 100 +
            "\ASSESSMENT TREND INTELLIGENCE TEST RUN\n" +
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