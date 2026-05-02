# Telegram LLM Assistant CLI — Implementation Plan

## Overview

A small Python CLI utility that orchestrates a conversation between an LLM and a human user via Telegram. The CLI takes a task description and success criteria as arguments, initiates a Telegram conversation, loops until the LLM judges the success criteria are met, then outputs the full transcript to STDOUT.

## Current State Analysis

Greenfield project. The repo contains only `CLAUDE.md` with the spec.

## Desired End State

A working CLI invocable as:

```bash
export TELEGRAM_BOT_TOKEN="..."
export TELEGRAM_CHAT_ID="..."
export LLM_MODEL="anthropic/claude-sonnet-4-20250514"  # any litellm model string

python -m text_assistant \
  --task "Collect the user's shipping address" \
  --success-criteria "We have their full name, street, city, state, and zip code"
```

The bot sends an opening message to the Telegram chat, has a multi-turn conversation with the user, and when the success criteria are satisfied, prints the transcript to STDOUT as JSON and exits cleanly.

### Verification

- Run the CLI with a simple task against a real Telegram bot + chat
- Confirm the bot initiates, converses, detects success, and exits
- Confirm the transcript appears on STDOUT as valid JSON
- Confirm the process exits with code 0 on success

## What We're NOT Doing

- Persistent state across runs (each invocation is one-shot)
- Web UI or dashboard
- Multi-user support (one chat ID per run)
- Streaming LLM responses
- Media/image handling (text only)
- Rate limiting or retry logic beyond basic timeouts
- The `/start` registration flow — we document that the user must have messaged the bot once before

## Implementation Approach

Single Python package (`text_assistant/`) with three small modules: LLM calls, Telegram conversation loop, and CLI entry point. Dependencies: `python-telegram-bot`, `litellm`, and stdlib only.

---

## Phase 1: Project Scaffolding

### Overview
Set up the Python package structure, dependencies, and entry point.

### Changes Required:

#### 1. `pyproject.toml`
**File**: `pyproject.toml`

```toml
[project]
name = "text-assistant"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "python-telegram-bot>=21.0,<22.0",
    "litellm>=1.60,<2.0",
]

[project.scripts]
text-assistant = "text_assistant.cli:main"
```

#### 2. Package structure
Create:
- `text_assistant/__init__.py` (empty)
- `text_assistant/cli.py` (stub)
- `text_assistant/llm.py` (stub)
- `text_assistant/bot.py` (stub)

### Success Criteria:

#### Automated Verification:
- [x] `pip install -e .` succeeds
- [x] `python -c "import text_assistant"` succeeds

---

## Phase 2: LLM Abstraction

### Overview
Thin wrapper around `litellm.completion` that provides two functions: generate a conversational reply and evaluate success criteria.

### Changes Required:

#### 1. `text_assistant/llm.py`
**File**: `text_assistant/llm.py`

Two functions, both calling `litellm.completion`:

```python
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
    response = completion(model=get_model(), messages=messages)
    return response.choices[0].message.content


# JSON schema for structured success evaluation
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
```

### Design Notes

- `generate_reply` receives the full conversation history each call so the LLM has full context.
- `check_success` uses **structured outputs** (`response_format` with a JSON schema) to get a reliable boolean `criteria_met` field, avoiding fragile free-text parsing. The `reasoning` field is required so the model "thinks" before deciding, but only `criteria_met` is used programmatically. litellm passes `response_format` through to the underlying provider (OpenAI, Anthropic, etc.).
- Both functions are synchronous — `litellm.completion` is sync. They'll be called from the async bot loop via `asyncio.to_thread` or `loop.run_in_executor`.

### Success Criteria:

#### Automated Verification:
- [x] `python -c "from text_assistant.llm import generate_reply, check_success"` succeeds
- [x] Unit test with mocked `litellm.completion` verifies `check_success` returns `True` when the mock response contains `{"criteria_met": true, "reasoning": "..."}` and `False` for `{"criteria_met": false, "reasoning": "..."}`

---

## Phase 3: Telegram Conversation Loop

### Overview
The core async loop: initialize the bot, send the opening message, listen for replies, call the LLM each turn, check success, and shut down cleanly.

### Changes Required:

#### 1. `text_assistant/bot.py`
**File**: `text_assistant/bot.py`

Uses the manual lifecycle pattern with `asyncio.Queue` to bridge Telegram handlers and the main loop.

```python
import asyncio
import json
import sys
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from text_assistant.llm import generate_reply, check_success


async def run_conversation(
    token: str,
    chat_id: int,
    task: str,
    success_criteria: str,
    timeout: int = 300,
) -> list[dict]:
    """
    Run a bot-initiated conversation until success criteria are met.
    Returns the conversation transcript as a list of message dicts.
    """
    response_queue: asyncio.Queue[str] = asyncio.Queue()
    conversation: list[dict] = []

    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message and update.message.text:
            await response_queue.put(update.message.text)

    # Build and start the application
    app = ApplicationBuilder().token(token).build()
    app.add_handler(
        MessageHandler(
            filters.Chat(chat_id=chat_id) & filters.TEXT & ~filters.COMMAND,
            handle_message,
        )
    )

    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)

    try:
        # Generate and send the opening message
        opening = await asyncio.to_thread(generate_reply, task, conversation)
        await app.bot.send_message(chat_id=chat_id, text=opening)
        conversation.append({"role": "assistant", "content": opening})

        while True:
            # Wait for user reply with timeout
            try:
                user_text = await asyncio.wait_for(
                    response_queue.get(), timeout=timeout
                )
            except asyncio.TimeoutError:
                # Send a timeout notice and exit
                await app.bot.send_message(
                    chat_id=chat_id,
                    text="(Session timed out due to inactivity.)",
                )
                break

            conversation.append({"role": "user", "content": user_text})

            # Check if success criteria are met
            criteria_met = await asyncio.to_thread(
                check_success, task, success_criteria, conversation
            )
            if criteria_met:
                break

            # Generate and send the next reply
            reply = await asyncio.to_thread(generate_reply, task, conversation)
            await app.bot.send_message(chat_id=chat_id, text=reply)
            conversation.append({"role": "assistant", "content": reply})

    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()

    return conversation
```

### Design Notes

- **Manual lifecycle** (`initialize`/`start`/`start_polling` ... `stop`/`shutdown`) gives us full control over the event loop and clean shutdown.
- **`asyncio.to_thread`** for LLM calls — `litellm.completion` is synchronous and blocking; this keeps the Telegram event loop responsive.
- **`drop_pending_updates=True`** prevents processing stale messages from before this run.
- **`filters.Chat(chat_id=...)`** ensures we only respond to the target user.
- **Timeout** prevents the bot from hanging forever if the user walks away. Default 300s (5 min) per reply.
- The conversation list uses OpenAI message format (`role`/`content`) since that's what litellm expects.

### Success Criteria:

#### Automated Verification:
- [x] `python -c "from text_assistant.bot import run_conversation"` succeeds

#### Manual Verification:
- [ ] Bot sends opening message to the correct Telegram chat
- [ ] Bot responds to user messages with LLM-generated replies
- [ ] Bot exits cleanly when success criteria are met
- [ ] Bot exits cleanly on timeout
- [ ] No stale messages from previous runs are processed

---

## Phase 4: CLI Entry Point

### Overview
Wire everything together with `argparse`. Parse args, read env vars, run the conversation, print the transcript.

### Changes Required:

#### 1. `text_assistant/cli.py`
**File**: `text_assistant/cli.py`

```python
import argparse
import asyncio
import json
import os
import sys

from text_assistant.bot import run_conversation


def main():
    parser = argparse.ArgumentParser(
        description="LLM-powered Telegram conversation assistant"
    )
    parser.add_argument(
        "--task",
        required=True,
        help="Description of what the assistant needs to accomplish",
    )
    parser.add_argument(
        "--success-criteria",
        required=True,
        help="How to determine when the task is complete",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Seconds to wait for each user reply (default: 300)",
    )
    args = parser.parse_args()

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Error: TELEGRAM_BOT_TOKEN environment variable is required", file=sys.stderr)
        sys.exit(1)

    chat_id_str = os.environ.get("TELEGRAM_CHAT_ID")
    if not chat_id_str:
        print("Error: TELEGRAM_CHAT_ID environment variable is required", file=sys.stderr)
        sys.exit(1)

    try:
        chat_id = int(chat_id_str)
    except ValueError:
        print("Error: TELEGRAM_CHAT_ID must be an integer", file=sys.stderr)
        sys.exit(1)

    transcript = asyncio.run(
        run_conversation(
            token=token,
            chat_id=chat_id,
            task=args.task,
            success_criteria=args.success_criteria,
            timeout=args.timeout,
        )
    )

    json.dump(transcript, sys.stdout, indent=2)
    print()  # trailing newline


if __name__ == "__main__":
    main()
```

#### 2. `text_assistant/__main__.py`
**File**: `text_assistant/__main__.py`

```python
from text_assistant.cli import main

main()
```

This enables `python -m text_assistant`.

### Success Criteria:

#### Automated Verification:
- [x] `python -m text_assistant --help` prints usage without errors
- [x] Missing env vars produce clear error messages to stderr and exit code 1

#### Manual Verification:
- [ ] Full end-to-end run: `python -m text_assistant --task "..." --success-criteria "..."` works against a real Telegram bot
- [ ] Transcript appears on STDOUT as valid JSON after success criteria are met
- [ ] Process exits with code 0

---

## Phase 5: Documentation & Hardening

### Overview
README with setup instructions (especially the Telegram `/start` prerequisite), and basic error handling for common failure modes.

### Changes Required:

#### 1. `README.md`
**File**: `README.md`

Document:
- What this tool does
- Prerequisites (Python 3.11+, Telegram bot token via BotFather, user must have `/start`'d the bot)
- How to get the `TELEGRAM_CHAT_ID` (message the bot, check logs or use `@userinfobot`)
- Environment variables: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `LLM_MODEL`
- Usage examples
- Supported LLM providers (link to litellm docs)

#### 2. Error handling additions to `bot.py`
- Catch `telegram.error.Forbidden` on the initial `send_message` and print a clear error ("Bot cannot message this chat — has the user sent /start to the bot?")
- Catch `litellm` exceptions and surface them clearly

### Success Criteria:

#### Automated Verification:
- [x] `pip install -e .` and `python -m text_assistant --help` work from a clean venv

#### Manual Verification:
- [ ] A new user can follow the README to set up and run the tool
- [ ] Clear error message when bot hasn't been `/start`'d by the user
- [ ] Clear error message when LLM API key is wrong or model string is invalid

---

## File Summary

| File | Action | Purpose |
|---|---|---|
| `pyproject.toml` | Create | Package config and dependencies |
| `text_assistant/__init__.py` | Create | Package marker (empty) |
| `text_assistant/__main__.py` | Create | `python -m` entry point |
| `text_assistant/cli.py` | Create | Argument parsing, env var validation, main() |
| `text_assistant/llm.py` | Create | LLM abstraction (generate_reply, check_success) |
| `text_assistant/bot.py` | Create | Telegram conversation loop |
| `README.md` | Create | Setup and usage docs |

## Environment Variables

| Variable | Required | Example | Notes |
|---|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Yes | `7123456789:AAF...` | From @BotFather |
| `TELEGRAM_CHAT_ID` | Yes | `123456789` | User's Telegram ID |
| `LLM_MODEL` | Yes | `anthropic/claude-sonnet-4-20250514` | Any litellm model string |
| `OPENAI_API_KEY` | If using OpenAI | `sk-...` | Set by litellm convention |
| `ANTHROPIC_API_KEY` | If using Anthropic | `sk-ant-...` | Set by litellm convention |

## References

- [python-telegram-bot v20 docs](https://docs.python-telegram-bot.org/en/v21.0/)
- [litellm docs](https://docs.litellm.ai/docs/)
- [litellm supported providers](https://docs.litellm.ai/docs/providers)
