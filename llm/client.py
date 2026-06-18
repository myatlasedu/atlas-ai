import httpx
import asyncio

from core.config import settings


async def chat_completion(
    messages: list
):

    timeout = httpx.Timeout(

        connect=10.0,

        read=60.0,

        write=10.0,

        pool=10.0
    )

    try:

        async with httpx.AsyncClient(
            timeout=timeout
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

    except httpx.ReadTimeout:

        raise Exception(
            "Ollama request timed out after 60 seconds."
        )

    except httpx.ConnectTimeout:

        raise Exception(
            "Unable to connect to Ollama server."
        )