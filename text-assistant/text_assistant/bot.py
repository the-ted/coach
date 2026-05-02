import asyncio
import sys

from telegram import Update
from telegram.error import Forbidden
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
        try:
            opening = await asyncio.to_thread(generate_reply, task, conversation)
        except Exception as e:
            print(f"Error: LLM call failed: {e}", file=sys.stderr)
            raise

        try:
            await app.bot.send_message(chat_id=chat_id, text=opening)
        except Forbidden:
            print(
                "Error: Bot cannot message this chat — has the user sent /start to the bot?",
                file=sys.stderr,
            )
            raise

        conversation.append({"role": "assistant", "content": opening})

        while True:
            # Wait for user reply with timeout
            try:
                user_text = await asyncio.wait_for(
                    response_queue.get(), timeout=timeout
                )
            except asyncio.TimeoutError:
                await app.bot.send_message(
                    chat_id=chat_id,
                    text="(Session timed out due to inactivity.)",
                )
                break

            conversation.append({"role": "user", "content": user_text})

            # Check if success criteria are met
            try:
                criteria_met = await asyncio.to_thread(
                    check_success, task, success_criteria, conversation
                )
            except Exception as e:
                print(f"Error: LLM call failed during success check: {e}", file=sys.stderr)
                raise

            if criteria_met:
                break

            # Generate and send the next reply
            try:
                reply = await asyncio.to_thread(generate_reply, task, conversation)
            except Exception as e:
                print(f"Error: LLM call failed: {e}", file=sys.stderr)
                raise

            await app.bot.send_message(chat_id=chat_id, text=reply)
            conversation.append({"role": "assistant", "content": reply})

    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()

    return conversation
