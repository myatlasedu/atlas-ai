import asyncio
import httpx
import time

# ===========================
# Configuration
# ===========================

URL = "https://stagingai.keyedsolution.com/api/ai/query"

CONCURRENT_REQUESTS = 1

PAYLOAD = {
    "query": "My Homework",
    "context": {
        "user_id": 406,
        "role": "student",
        "campus_id": 1,
        "student_id": 356,
        "enrollment_id": 351,
        "academic_class_id": 3,
    },
}

HEADERS = {
    "accept": "application/json",
    "Content-Type": "application/json",
}


# ===========================
# Worker
# ===========================

async def make_request(client, request_no):

    start = time.perf_counter()

    try:

        response = await client.post(
            URL,
            json=PAYLOAD,
            headers=HEADERS,
        )

        elapsed = time.perf_counter() - start

        print(
            f"[{request_no:02}] "
            f"{response.status_code} "
            f"{elapsed:.2f}s"
        )

        return elapsed

    except Exception as e:

        elapsed = time.perf_counter() - start

        print(
            f"[{request_no:02}] FAILED "
            f"{elapsed:.2f}s "
            f"{e}"
        )

        return None


# ===========================
# Main
# ===========================

async def main():

    timeout = httpx.Timeout(300)

    async with httpx.AsyncClient(timeout=timeout) as client:

        overall_start = time.perf_counter()

        tasks = [

            make_request(
                client,
                i + 1,
            )

            for i in range(CONCURRENT_REQUESTS)
        ]

        results = await asyncio.gather(*tasks)

        total_time = time.perf_counter() - overall_start

    successful = [r for r in results if r is not None]

    print("\n========== SUMMARY ==========")

    print(f"Concurrent Requests : {CONCURRENT_REQUESTS}")
    print(f"Successful          : {len(successful)}")
    print(f"Failed              : {CONCURRENT_REQUESTS - len(successful)}")
    print(f"Total Time          : {total_time:.2f}s")

    if successful:
        print(f"Average             : {sum(successful)/len(successful):.2f}s")
        print(f"Fastest             : {min(successful):.2f}s")
        print(f"Slowest             : {max(successful):.2f}s")


if __name__ == "__main__":
    asyncio.run(main())