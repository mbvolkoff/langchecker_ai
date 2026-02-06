"""Telegram bot for language checking using AI agent."""

import html
import logging
import os
import re

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from main import process_text
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g., https://your-domain.com or https://1.2.3.4:8443
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "8443"))
WEBHOOK_SSL_CERT = os.getenv("WEBHOOK_SSL_CERT")  # Path to SSL certificate (cert.pem)
WEBHOOK_SSL_KEY = os.getenv("WEBHOOK_SSL_KEY")  # Path to SSL private key (private.key)


def markdown_to_telegram_html(text: str) -> str:
    """Convert standard markdown to Telegram-compatible HTML.

    Handles bold, italic, strikethrough, code blocks, inline code, and links.
    Falls back gracefully — any unsupported syntax is left as plain text.
    """
    # Escape HTML special chars first so we don't break tags we insert later
    text = html.escape(text)

    # Fenced code blocks: ```lang\n...\n``` → <pre>...</pre>
    text = re.sub(
        r"```(?:\w*)\n(.*?)```", r"<pre>\1</pre>", text, flags=re.DOTALL
    )

    # Inline code: `...` → <code>...</code>
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)

    # Bold: **text** or __text__  →  <b>text</b>
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"__(.+?)__", r"<b>\1</b>", text)

    # Italic: *text* or _text_  →  <i>text</i>
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    text = re.sub(r"(?<!\w)_(.+?)_(?!\w)", r"<i>\1</i>", text)

    # Strikethrough: ~~text~~ → <s>text</s>
    text = re.sub(r"~~(.+?)~~", r"<s>\1</s>", text)

    # Markdown links: [text](url) → <a href="url">text</a>
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)

    return text


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    await update.message.reply_text(
        "Hello! I'm a language checker bot.\n\n"
        "Send me any text and I'll check its grammar and correctness.\n"
        "I'll identify the language automatically and provide suggestions if needed."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    await update.message.reply_text(
        "How to use this bot:\n\n"
        "1. Simply send me any text\n"
        "2. I'll identify the language\n"
        "3. I'll check grammar and correctness\n"
        "4. I'll provide suggestions if needed\n\n"
        "Commands:\n"
        "/start - Start the bot\n"
        "/help - Show this help message"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming text messages."""
    user_text = update.message.text
    user = update.effective_user
    logger.info(f"Received message from {user.id} ({user.username}): {user_text[:50]}...")
    
    # Send typing indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        # Process the text using the AI agent
        response = process_text(user_text)

        # Convert markdown to Telegram HTML and send formatted message
        try:
            formatted = markdown_to_telegram_html(response)
            await update.message.reply_text(formatted, parse_mode=ParseMode.HTML)
        except Exception:
            # If HTML parsing fails, fall back to plain text
            logger.warning("Failed to send formatted message, falling back to plain text")
            await update.message.reply_text(response)
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        await update.message.reply_text(
            "Sorry, an error occurred while processing your text. Please try again later."
        )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors."""
    logger.error(f"Update {update} caused error {context.error}")


def create_application() -> Application:
    """Create and configure the bot application."""
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set")
    
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    return application


def run_webhook():
    """Run the bot using webhook (for VPS deployment)."""
    if not WEBHOOK_URL:
        raise ValueError("WEBHOOK_URL environment variable is not set")
    
    application = create_application()
    
    webhook_kwargs = {
        "listen": "0.0.0.0",
        "port": WEBHOOK_PORT,
        "url_path": TELEGRAM_BOT_TOKEN,
        "webhook_url": f"{WEBHOOK_URL}/{TELEGRAM_BOT_TOKEN}",
    }
    
    # Add SSL certificate and key if provided (required for self-signed certs / direct HTTPS)
    if WEBHOOK_SSL_CERT and WEBHOOK_SSL_KEY:
        webhook_kwargs["cert"] = WEBHOOK_SSL_CERT
        webhook_kwargs["key"] = WEBHOOK_SSL_KEY
        logger.info(f"Using SSL cert: {WEBHOOK_SSL_CERT}, key: {WEBHOOK_SSL_KEY}")
    else:
        logger.warning(
            "No SSL cert/key provided. The bot will serve plain HTTP. "
            "Make sure a reverse proxy handles TLS termination."
        )
    
    # Run with webhook
    application.run_webhook(**webhook_kwargs)


def run_polling():
    """Run the bot using polling (for local development)."""
    application = create_application()
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--polling":
        logger.info("Starting bot in polling mode (development)...")
        run_polling()
    else:
        logger.info("Starting bot in webhook mode (production)...")
        run_webhook()
