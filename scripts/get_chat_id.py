# scripts/get_chat_id.py
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user's chat ID"""
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        f"🤖 Your Chat ID: `{chat_id}`\n\n"
        f"Add this to your `.env` file:\n"
        f"`TELEGRAM_CHAT_ID={chat_id}`",
        parse_mode="Markdown"
    )

async def main():
    # Get token from environment
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("id", get_chat_id))
    
    print("Bot started. Send /id to get your chat ID...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
