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
