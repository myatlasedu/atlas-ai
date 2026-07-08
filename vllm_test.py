import asyncio
import time
import httpx

URL = "http://142.93.153.43:8000/v1/chat/completions"

MODEL = "Qwen/Qwen2.5-7B-Instruct"

PROMPT = "Say hello in one sentence."


async def main():

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": PROMPT,
            }
        ],
        "temperature": 0.3,
        "max_tokens": 20,
    }

    timeout = httpx.Timeout(300)

    async with httpx.AsyncClient(timeout=timeout) as client:

        start = time.perf_counter()

        response = await client.post(
            URL,
            json=payload,
        )

        elapsed = time.perf_counter() - start

    print("=" * 60)
    print(f"Status : {response.status_code}")
    print(f"Time   : {elapsed:.3f} sec")
    print("=" * 60)

    data = response.json()

    print("\nCompletion:\n")

    print(data["choices"][0]["message"]["content"])

    print("\nUsage:\n")

    print(data["usage"])


if __name__ == "__main__":
    asyncio.run(main())