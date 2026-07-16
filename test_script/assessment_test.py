# test_assessment_queries.py

import json
import time
import requests
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

    # =====================================================
    # PERFORMANCE ANALYSIS
    # =====================================================

    "How am I performing in assessments?",
    "Analyze my assessment performance.",
    "Give me an assessment performance summary.",
    "How are my assessment results overall?",
    "Am I doing well in assessments?",
    "How strong is my assessment performance?",
    "Review my assessment performance.",
    "Provide an analysis of my assessment results.",
    "What do my assessment results indicate?",
    "How would you evaluate my assessment performance?",

    # =====================================================
    # IMPROVEMENT / FOCUS
    # =====================================================

    "What should I improve in assessments?",
    "What should I focus on next?",
    "Which assessment needs the most attention?",
    "What assessment should I revisit?",
    "Where should I focus my preparation?",
    "What is my weakest assessment area?",
    "What assessment is holding me back?",
    "Which test result needs improvement?",
    "What should I work on before the next assessment?",
    "What can I do to improve my assessment performance?",

    # =====================================================
    # LOWEST ASSESSMENT INTERPRETATION
    # =====================================================

    "Why is my lowest assessment score low?",
    "Explain my weakest assessment.",
    "Why did I perform poorly in my weakest assessment?",
    "What can I learn from my weakest assessment?",
    "Analyze my lowest scoring assessment.",
    "What went wrong in my weakest test?",
    "What should I improve from my lowest assessment?",
    "How can I improve my weakest assessment result?",

    # =====================================================
    # TREND ANALYSIS
    # =====================================================

    "Am I improving in assessments?",
    "Are my assessment scores getting better?",
    "How consistent are my assessment scores?",
    "Do you see improvement in my test results?",
    "What trends do you notice in my assessments?",
    "How stable is my assessment performance?",
    "Are my marks improving over time?",
    "Is my performance trending upward or downward?",

    # =====================================================
    # FEEDBACK INTERPRETATION
    # =====================================================

    "What does my teacher feedback suggest?",
    "Summarize my assessment feedback.",
    "What are the key themes in my teacher feedback?",
    "What can I learn from recent assessment feedback?",
    "Analyze my teacher comments.",
    "What do my teachers think about my assessment performance?",
    "What improvements are suggested in my feedback?",

    # =====================================================
    # GENERIC REASONING
    # =====================================================

    "Assessment overview",
    "Assessment summary",
    "Review my assessments",
    "Explain my assessment results",
    "What do my assessments say about my performance?",
    "Give me an assessment dashboard summary.",
    "Summarize my assessment history.",
    "What insights can you provide from my assessments?",

    # =====================================================
    # HALLUCINATION TESTS
    # =====================================================

    "How am I performing in assessments? Do not talk about attendance.",
    "Analyze my assessments only.",
    "Assessment performance without considering homework.",
    "Focus only on assessment data.",
    "Use only my assessment results for analysis.",
    "Assessment analysis only. Ignore Atlas score.",
    "Explain my assessment performance without discussing attendance.",
    "Review my test results only.",
    "Assessment insights only.",
    "Analyze assessments and nothing else.",

    # =====================================================
    # EDGE CASES
    # =====================================================

    "Why are my scores dropping?",
    "What is causing my weaker assessment performance?",
    "How can I raise my average assessment score?",
    "What are my strengths in assessments?",
    "What are my weaknesses in assessments?",
    "What is the biggest risk in my assessment performance?",
    "Which assessment contributes most to my average?",
    "What should be my next academic focus?",
    "How prepared am I for future assessments?",
    "What concerns do you see in my assessment record?"
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
        f"assessment_test_log_{timestamp}.txt"
    )

    with open(
        logfile,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(
            "=" * 100 +
            "\nASSESSMENT INTELLIGENCE TEST RUN\n" +
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