

from openai import AsyncOpenAI

from core.config import settings


client = AsyncOpenAI(
    api_key=settings.LLM_API_KEY,
    base_url=f"{settings.LLM_BASE_URL}/v1",
)

async def chat_completion(messages):

    response = await client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=messages,
        temperature=0.1,
        max_tokens=500,
        timeout=60
    )

    return {
        "message": {
            "content": response.choices[0].message.content
        }
    }