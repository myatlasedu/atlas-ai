import logging

from openai import AsyncOpenAI

from core.config import settings


logger = logging.getLogger(__name__)


client = AsyncOpenAI(
    api_key=settings.LLM_API_KEY,
    base_url=f"{settings.LLM_BASE_URL}/v1",
)

async def chat_completion(
    messages,
    expect_json: bool = False,
):

    kwargs = {
        "model": settings.LLM_MODEL,
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": 500,
        "timeout": 60,
    }

    if expect_json:
        kwargs["response_format"] = {"type": "json_object"}

    try:
        response = await _create(**kwargs)
    except Exception as e:
        if expect_json:
            logger.warning(
                "response_format json_object unsupported (%s). Retrying without it.",
                e,
            )
            kwargs.pop("response_format", None)
            response = await _create(**kwargs)
        else:
            raise

    return {
        "message": {
            "content": response.choices[0].message.content
        }
    }


async def _create(**kwargs):
    response = await client.chat.completions.create(**kwargs)
    return response