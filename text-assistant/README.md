# text-assistant

A small Python CLI that orchestrates a conversation between an LLM and a human user via Telegram. Give it a task and success criteria — it starts a chat, converses until the criteria are met, then prints the transcript to STDOUT as JSON.

## Prerequisites

- Python 3.11+
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- The user must have sent `/start` to the bot at least once before running
- An API key for your chosen LLM provider (e.g. `ANTHROPIC_API_KEY`)

## Getting the Chat ID

Message your bot in Telegram, then either:
- Use [@userinfobot](https://t.me/userinfobot) to get your numeric user ID
- Or check the bot's update logs via the Telegram Bot API

## Install

```bash
pip install -e .
```

## Environment Variables

| Variable | Required | Example |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Yes | `7123456789:AAF...` |
| `TELEGRAM_CHAT_ID` | Yes | `123456789` |
| `LLM_MODEL` | Yes | `anthropic/claude-sonnet-4-20250514` |
| `ANTHROPIC_API_KEY` | If using Anthropic | `sk-ant-...` |
| `OPENAI_API_KEY` | If using OpenAI | `sk-...` |

`LLM_MODEL` accepts any [litellm model string](https://docs.litellm.ai/docs/providers).

## Usage

```bash
export TELEGRAM_BOT_TOKEN="..."
export TELEGRAM_CHAT_ID="..."
export LLM_MODEL="anthropic/claude-sonnet-4-20250514"

python -m text_assistant \
  --task "Collect the user's shipping address" \
  --success-criteria "We have their full name, street, city, state, and zip code"
```

The bot sends an opening message, has a multi-turn conversation, and when the success criteria are satisfied, prints the transcript to STDOUT as JSON and exits.

### Options

- `--task` (required): What the assistant needs to accomplish
- `--success-criteria` (required): How to determine when the task is complete
- `--timeout`: Seconds to wait for each user reply (default: 300)

## How It Works

1. The CLI parses args and reads env vars
2. The bot sends an LLM-generated opening message to the Telegram chat
3. On each user reply, the LLM evaluates whether the success criteria are met
4. If not met, the LLM generates a follow-up message and sends it
5. When criteria are met, the full transcript is printed to STDOUT as JSON and the process exits with code 0
6. If the user doesn't reply within the timeout, the bot sends a timeout notice and exits
