from __future__ import annotations


def build_llm_context(
    results: dict,
) -> dict:

    context = {}

    for tool_result in results.values():

        if not isinstance(
            tool_result,
            dict,
        ):
            continue

        module = tool_result.get(
            "module"
        )

        if not module:
            continue

        llm_context = tool_result.get(
            "llm_context"
        )

        if llm_context is not None:

            context[module] = llm_context

            continue

        direct_answer = tool_result.get(
            "direct_answer"
        )

        if direct_answer is not None:

            context[module] = {

                "direct_answer":
                    direct_answer
            }

    return context