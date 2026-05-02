import json
import os
from litellm import completion


def get_model() -> str:
    """Return the model string from env, e.g. 'anthropic/claude-sonnet-4-20250514'."""
    model = os.environ.get("LLM_MODEL")
    if not model:
        raise RuntimeError("LLM_MODEL environment variable is required")
    return model


def generate_reply(task: str, conversation: list[dict]) -> str:
    """
    Given the task description and conversation history,
    return the next assistant message.

    conversation is in OpenAI message format:
    [{"role": "user"|"assistant", "content": "..."}]
    """
    system_prompt = (
        f"You are an assistant communicating with a user via Telegram. "
        f"Your task: {task}\n\n"
        f"Be concise and conversational. Ask for information you need "
        f"to complete the task. Do not explain that you are an AI unless asked."
    )
    messages = [{"role": "system", "content": system_prompt}] + conversation
    # Anthropic requires at least one non-system message.
    # On the first turn the conversation is empty, so add a kick-off prompt.
    if not conversation:
        messages.append({"role": "user", "content": "Begin the conversation."})
    response = completion(model=get_model(), messages=messages)
    return response.choices[0].message.content


SUCCESS_EVAL_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "success_evaluation",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "criteria_met": {
                    "type": "boolean",
                    "description": "Whether all success criteria have been fully met",
                },
                "reasoning": {
                    "type": "string",
                    "description": "Brief explanation of why criteria are or are not met",
                },
            },
            "required": ["criteria_met", "reasoning"],
            "additionalProperties": False,
        },
    },
}


def check_success(task: str, success_criteria: str, conversation: list[dict]) -> bool:
    """
    Evaluate whether the success criteria have been met
    based on the conversation so far.

    Uses structured outputs (response_format) to get a reliable
    boolean result instead of parsing free text.
    Returns True if criteria are satisfied.
    """
    transcript_text = "\n".join(
        f"{m['role'].upper()}: {m['content']}" for m in conversation
    )
    system_prompt = (
        "You are an evaluator. You will be given a task description, "
        "success criteria, and a conversation transcript. "
        "Determine whether the success criteria have been fully met."
    )
    user_prompt = (
        f"Task: {task}\n\n"
        f"Success Criteria: {success_criteria}\n\n"
        f"Conversation Transcript:\n{transcript_text}\n\n"
        f"Have the success criteria been fully met?"
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    response = completion(
        model=get_model(),
        messages=messages,
        response_format=SUCCESS_EVAL_SCHEMA,
    )
    result = json.loads(response.choices[0].message.content)
    return result["criteria_met"]
