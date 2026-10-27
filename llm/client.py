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
    max_tokens: int = 1024,
    thinking: bool = False,
):
    kwargs = {
        "model": settings.LLM_MODEL,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": max_tokens,
        "timeout": 60,
        "extra_body": {
            "chat_template_kwargs": {
                "enable_thinking": thinking,
            }
        },
    }

    if expect_json:
        kwargs["response_format"] = {"type": "json_object"}

    try:
        response = await _create(**kwargs)

    except Exception as exc:
        error_message = str(exc).lower()

        # Retry without JSON response format only when the server
        # explicitly rejects that parameter.
        json_format_unsupported = (
            expect_json
            and "response_format" in error_message
            and any(
                marker in error_message
                for marker in (
                    "unsupported",
                    "not supported",
                    "unrecognized",
                    "unknown parameter",
                )
            )
        )

        if not json_format_unsupported:
            raise

        logger.warning(
            "JSON response format unsupported; retrying without it."
        )

        kwargs.pop("response_format", None)
        response = await _create(**kwargs)

    return {
        "message": {
            "content": response.choices[0].message.content
        }
    }


async def _create(**kwargs):
    return await client.chat.completions.create(**kwargs)