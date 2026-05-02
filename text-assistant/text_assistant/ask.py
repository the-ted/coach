"""
Single-turn Telegram ask utility.

Sends one message to the configured Telegram chat, waits for the next user
reply, prints that reply to stdout, and exits. Unlike `text_assistant.cli`,
this does not call an LLM — the caller (e.g. a Claude sub-agent) is
responsible for choosing the question and interpreting the answer.

Usage:
    python -m text_assistant.ask --message "Your question" [--timeout 600]

Env vars: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
"""

import argparse
import asyncio
import os
import sys

from telegram import Update
from telegram.error import Forbidden
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters


async def ask_once(token: str, chat_id: int, message: str, timeout: int) -> str:
    response_queue: asyncio.Queue[str] = asyncio.Queue()

    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message and update.message.text:
            await response_queue.put(update.message.text)

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
        try:
            await app.bot.send_message(chat_id=chat_id, text=message)
        except Forbidden:
            print(
                "Error: Bot cannot message this chat — has the user sent /start to the bot?",
                file=sys.stderr,
            )
            raise

        return await asyncio.wait_for(response_queue.get(), timeout=timeout)
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


def main():
    parser = argparse.ArgumentParser(description="Single-turn Telegram ask")
    parser.add_argument("--message", required=True, help="Message to send")
    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="Seconds to wait for the user reply (default: 600)",
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

    try:
        reply = asyncio.run(
            ask_once(
                token=token,
                chat_id=chat_id,
                message=args.message,
                timeout=args.timeout,
            )
        )
    except asyncio.TimeoutError:
        print("Error: timed out waiting for user reply", file=sys.stderr)
        sys.exit(2)

    sys.stdout.write(reply)
    sys.stdout.flush()


if __name__ == "__main__":
    main()
