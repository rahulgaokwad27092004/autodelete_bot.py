from telegram import Update, ChatPermissions
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
)
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import logging

# Bot token here
BOT_TOKEN = "7698290595:AAHO-M-q2_D3wMUYDprq00jaZ_Gk1CG2ZqM"

# In-memory storage for delete time per chat
chat_delete_times = {}
message_store = []

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

# Scheduler for deleting messages
scheduler = BackgroundScheduler()
scheduler.start()

# Command: /setdeletetime 30
async def set_delete_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1 or not context.args[0].isdigit():
        await update.message.reply_text("Usage: /setdeletetime <seconds>")
        return

    seconds = int(context.args[0])
    chat_id = update.effective_chat.id
    chat_delete_times[chat_id] = seconds
    await update.message.reply_text(f"Messages will now be deleted after {seconds} seconds.")

# Track and schedule deletion of messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    chat_id = message.chat_id

    if chat_id not in chat_delete_times:
        return  # Do nothing if delete time is not set

    delete_after = chat_delete_times[chat_id]
    delete_time = datetime.now() + timedelta(seconds=delete_after)

    # Save message for deletion
    message_store.append((chat_id, message.message_id))

    # Schedule deletion
    scheduler.add_job(
        delete_message,
        'date',
        run_date=delete_time,
        args=[context.application, chat_id, message.message_id],
        id=f"{chat_id}_{message.message_id}",
        replace_existing=True
    )

async def delete_message(app, chat_id, message_id):
    try:
        await app.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        print(f"Failed to delete message {message_id}: {e}")

# Run bot
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("setdeletetime", set_delete_time))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("Bot is running...")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
