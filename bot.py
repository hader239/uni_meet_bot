"""
Telegram Student Meetup Bot

A bot for university students to create profiles and meet fellow students.
"""

import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)

from config import BOT_TOKEN, PORT, WEBHOOK_URL
import database as db
from constants import (
    HOMEPAGE, AWAITING_PHOTOS, AWAITING_UNIVERSITY, AWAITING_PROGRAM, AWAITING_BIO,
    EDIT_MENU, EDIT_PHOTOS, EDIT_UNIVERSITY, EDIT_PROGRAM, EDIT_BIO,
    BTN_DONE_PHOTOS, BTN_CANCEL_EDITING,
)
from handlers import (
    start_handler, homepage_handler, help_handler, cancel_handler,
    receive_photo_handler, done_photos_handler,
    receive_university_handler, receive_program_handler, receive_bio_handler,
    edit_menu_handler,
    edit_photos_handler, edit_photos_done_handler,
    edit_university_handler, edit_program_handler, edit_bio_handler,
    cancel_editing_handler,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Start the bot."""
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set!")
        return
    
    # Database initialization and bot commands setup
    async def post_init(application):
        # Initialize database (if exists)
        created = await db.init_db()
        if created:
            logger.info("Database tables created")
        else:
            logger.info("Database tables already exist")
        
        # Set bot commands (shows in menu button)
        from telegram import BotCommand
        commands = [
            BotCommand("start", "Start the bot / Go to homepage"),
            BotCommand("help", "Show help message"),
        ]
        await application.bot.set_my_commands(commands)
        logger.info("Bot commands registered")
    
    # Create application with post_init hook
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    
    # Create conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start_handler)],
        states={
            HOMEPAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, homepage_handler),
            ],
            AWAITING_PHOTOS: [
                MessageHandler(filters.PHOTO, receive_photo_handler),
                MessageHandler(filters.Regex(f"^{BTN_DONE_PHOTOS}$"), done_photos_handler),
            ],
            AWAITING_UNIVERSITY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_university_handler),
            ],
            AWAITING_PROGRAM: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_program_handler),
            ],
            AWAITING_BIO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_bio_handler),
            ],
            EDIT_MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_menu_handler),
            ],
            EDIT_PHOTOS: [
                MessageHandler(filters.PHOTO, edit_photos_handler),
                MessageHandler(filters.Regex(f"^{BTN_DONE_PHOTOS}$"), edit_photos_done_handler),
                MessageHandler(filters.Regex(f"^{BTN_CANCEL_EDITING}$"), cancel_editing_handler),
            ],
            EDIT_UNIVERSITY: [
                MessageHandler(filters.Regex(f"^{BTN_CANCEL_EDITING}$"), cancel_editing_handler),
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_university_handler),
            ],
            EDIT_PROGRAM: [
                MessageHandler(filters.Regex(f"^{BTN_CANCEL_EDITING}$"), cancel_editing_handler),
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_program_handler),
            ],
            EDIT_BIO: [
                MessageHandler(filters.Regex(f"^{BTN_CANCEL_EDITING}$"), cancel_editing_handler),
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_bio_handler),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_handler), CommandHandler("start", start_handler)],
    )
    
    # Add handlers
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("help", help_handler))
    
    # Start the bot
    logger.info("Starting bot...")
    
    if WEBHOOK_URL:
        # Production mode: use webhooks (Railway)
        logger.info(f"Running with webhooks on port {PORT}")
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=BOT_TOKEN,
            webhook_url=f"https://{WEBHOOK_URL}/{BOT_TOKEN}",
            allowed_updates=Update.ALL_TYPES,
        )
    else:
        # Development mode: use long polling
        logger.info("Running with long polling (no WEBHOOK_URL set)")
        application.run_polling(allowed_updates=Update.ALL_TYPES, timeout=0)


if __name__ == "__main__":
    main()
