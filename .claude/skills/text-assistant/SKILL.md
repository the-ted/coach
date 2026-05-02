---
name: text-assistant
description: "Collect information from a user via Telegram using the text-assistant utility."
---

You collect information from a user by running the `text-assistant` Python utility, which conducts an LLM-powered Telegram conversation.

The user (or a calling skill) will describe what information needs to be gathered. Your job is to translate that into a task description and success criteria, run the utility, and return the transcript.

# Steps

1. **Clarify the objective.** From the user's request, determine:
   - **Task**: a plain-English description of what the Telegram conversation should accomplish (e.g., "Collect the user's preferred meeting time and any scheduling constraints").
   - **Success criteria**: a plain-English description of what counts as complete (e.g., "We have a specific day, time, and any conflicts the user mentioned").

   If the user's request is ambiguous, ask them to clarify before proceeding.

2. **Run the utility.** Execute:

   ```
   python -m text_assistant --task "TASK" --success-criteria "SUCCESS_CRITERIA"
   ```

   from the `~/org/text-assistant` directory.

   The utility requires these environment variables (they should already be set):
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - `LLM_MODEL`
   - An appropriate API key (`ANTHROPIC_API_KEY` or `OPENAI_API_KEY`)

   You may pass `--timeout SECONDS` if the user requests a custom timeout (default is 300s).

   **This command is long-running** — it blocks while waiting for the Telegram user to respond. Use a generous timeout (at least 600000ms) when calling Bash.

3. **Return the transcript.** The utility prints a JSON array of `{"role": "assistant"|"user", "content": "..."}` messages to stdout. Parse this and present the conversation back to the caller in a readable format, along with the raw JSON if they need it for further processing.

# Notes

- If the command exits with an error, report the stderr output to the user.
- Do not fabricate transcript data. Only report what the utility actually returned.
