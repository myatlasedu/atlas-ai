import httpx

from core.config import settings


async def chat_completion(
    messages: list
):

    async with httpx.AsyncClient(
        timeout=120
    ) as client:

        response = await client.post(
            f"{settings.OLLAMA_BASE_URL}/api/chat",
            json={
                "model": settings.OLLAMA_MODEL,
                "messages": messages,
                "stream": False
            }
        )

        response.raise_for_status()

        return response.json()