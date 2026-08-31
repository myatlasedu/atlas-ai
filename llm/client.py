from openai import AsyncOpenAI

from core.config import settings


client = AsyncOpenAI(
    api_key=settings.LLM_API_KEY,
    base_url=f"{settings.LLM_BASE_URL}/v1",
)


async def chat_completion(
    messages,
    thinking=False,
):

    kwargs = {
        "model": settings.LLM_MODEL,
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": 500,
        "timeout": 60,
    }

    kwargs["extra_body"] = {
        "chat_template_kwargs": {
            "enable_thinking": thinking,
        }
    }

    response = await client.chat.completions.create(
        **kwargs
    )

    return {
        "message": {
            "content": (
                response
                .choices[0]
                .message
                .content
            )
        }
    }