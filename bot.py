"""
Telegram Student Meetup Bot

A bot for university students to create profiles and meet fellow students.
"""

import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InputMediaPhoto
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

from config import BOT_TOKEN, MAX_PHOTOS, PORT, WEBHOOK_URL
import database as db

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
(
    HOMEPAGE,
    AWAITING_PHOTOS,
    AWAITING_UNIVERSITY,
    AWAITING_PROGRAM,
    AWAITING_BIO,
    EDIT_MENU,
    EDIT_PHOTOS,
    EDIT_UNIVERSITY,
    EDIT_PROGRAM,
    EDIT_BIO,
) = range(10)

# Button text constants
BTN_FILL_PROFILE = "📝 Fill Profile"
BTN_EDIT_PROFILE = "✏️ Edit Profile"
BTN_VIEW_PROFILE = "👤 View My Profile"
BTN_BACK_HOME = "🔙 Back to Home"
BTN_DONE_PHOTOS = "✅ Done with Photos"
BTN_EDIT_PHOTOS = "📷 Photos"
BTN_EDIT_UNIVERSITY = "🏫 University"
BTN_EDIT_PROGRAM = "📚 Program"
BTN_EDIT_BIO = "📝 Bio"


def get_homepage_keyboard(has_profile: bool = False) -> ReplyKeyboardMarkup:
    """Get the homepage keyboard based on whether user has a profile."""
    if has_profile:
        keyboard = [
            [BTN_EDIT_PROFILE, BTN_VIEW_PROFILE],
        ]
    else:
        keyboard = [
            [BTN_FILL_PROFILE],
        ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_edit_menu_keyboard() -> ReplyKeyboardMarkup:
    """Get the edit menu keyboard."""
    keyboard = [
        [BTN_EDIT_PHOTOS, BTN_EDIT_UNIVERSITY],
        [BTN_EDIT_PROGRAM, BTN_EDIT_BIO],
        [BTN_BACK_HOME],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_photo_upload_keyboard() -> ReplyKeyboardMarkup:
    """Get the keyboard for photo upload state."""
    keyboard = [
        [BTN_DONE_PHOTOS],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /start command - show homepage."""
    user = update.effective_user
    has_profile = await db.profile_exists(user.id)
    
    welcome_text = (
        f"👋 Welcome, {user.first_name}!\n\n"
        "🎓 *Student Meetup Bot*\n\n"
        "Connect with fellow students from your university!\n\n"
    )
    
    if has_profile:
        welcome_text += "What would you like to do?"
    else:
        welcome_text += "Get started by filling out your profile!"
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_homepage_keyboard(has_profile),
        parse_mode="Markdown",
    )
    return HOMEPAGE


async def homepage_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle homepage button presses."""
    text = update.message.text
    user = update.effective_user
    
    if text == BTN_FILL_PROFILE:
        # Initialize photo collection
        context.user_data["photos"] = []
        
        await update.message.reply_text(
            f"📷 *Step 1/4: Photos*\n\n"
            f"Upload up to {MAX_PHOTOS} photos of yourself.\n"
            f"Photos uploaded: 0/{MAX_PHOTOS}\n\n"
            f"Send photos one by one, or tap 'Done' to skip/continue.",
            reply_markup=get_photo_upload_keyboard(),
            parse_mode="Markdown",
        )
        return AWAITING_PHOTOS
    
    elif text == BTN_EDIT_PROFILE:
        await update.message.reply_text(
            "✏️ *Edit Profile*\n\n"
            "What would you like to change?",
            reply_markup=get_edit_menu_keyboard(),
            parse_mode="Markdown",
        )
        return EDIT_MENU
    
    elif text == BTN_VIEW_PROFILE:
        profile = await db.get_profile(user.id)
        
        if not profile:
            await update.message.reply_text(
                "❌ You don't have a profile yet!",
                reply_markup=get_homepage_keyboard(False),
            )
            return HOMEPAGE
        
        profile_text = (
            f"👤 *Your Profile*\n\n"
            f"🏫 *University:* {profile['university'] or 'Not set'}\n"
            f"📚 *Program:* {profile['program'] or 'Not set'}\n"
            f"📝 *About:* {profile['bio'] or 'Not set'}"
        )
        
        # If there are photos, send them with caption
        if profile["photos"]:
            if len(profile["photos"]) == 1:
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=profile["photos"][0],
                    caption=profile_text,
                    parse_mode="Markdown",
                    reply_markup=get_homepage_keyboard(True),
                )
            else:
                media = [
                    InputMediaPhoto(
                        media=profile["photos"][0],
                        caption=profile_text,
                        parse_mode="Markdown",
                    )
                ]
                media.extend([InputMediaPhoto(file_id) for file_id in profile["photos"][1:]])
                await context.bot.send_media_group(
                    chat_id=update.effective_chat.id,
                    media=media,
                )
                await update.message.reply_text(
                    "What would you like to do?",
                    reply_markup=get_homepage_keyboard(True),
                )
        else:
            await update.message.reply_text(
                profile_text + "\n📷 *Photos:* None uploaded",
                reply_markup=get_homepage_keyboard(True),
                parse_mode="Markdown",
            )
        return HOMEPAGE
    
    # Unknown input - show homepage again
    has_profile = await db.profile_exists(user.id)
    await update.message.reply_text(
        "Please use the buttons below.",
        reply_markup=get_homepage_keyboard(has_profile),
    )
    return HOMEPAGE


async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle photo uploads during profile creation."""
    photos = context.user_data.get("photos", [])
    
    if len(photos) >= MAX_PHOTOS:
        await update.message.reply_text(
            f"❌ You've already uploaded {MAX_PHOTOS} photos. "
            f"Tap 'Done' to continue.",
            reply_markup=get_photo_upload_keyboard(),
        )
        return AWAITING_PHOTOS
    
    # Get the largest photo size
    photo = update.message.photo[-1]
    photos.append(photo.file_id)
    context.user_data["photos"] = photos
    
    remaining = MAX_PHOTOS - len(photos)
    
    if remaining > 0:
        await update.message.reply_text(
            f"📷 Photo {len(photos)}/{MAX_PHOTOS} received!\n\n"
            f"You can upload {remaining} more photo(s), or tap 'Done' to continue.",
            reply_markup=get_photo_upload_keyboard(),
        )
    else:
        await update.message.reply_text(
            f"📷 All {MAX_PHOTOS} photos received!\n\n"
            f"Tap 'Done' to continue to the next step.",
            reply_markup=get_photo_upload_keyboard(),
        )
    return AWAITING_PHOTOS


async def done_photos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle 'Done with Photos' button."""
    photo_count = len(context.user_data.get("photos", []))
    
    await update.message.reply_text(
        f"✅ {photo_count} photo(s) saved!\n\n"
        f"🏫 *Step 2/4: University*\n\n"
        f"Please enter the name of your university:",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="Markdown",
    )
    return AWAITING_UNIVERSITY


async def receive_university(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle university input."""
    context.user_data["university"] = update.message.text
    
    await update.message.reply_text(
        f"✅ University: {update.message.text}\n\n"
        f"📚 *Step 3/4: Program*\n\n"
        f"Please enter your program/major:",
        parse_mode="Markdown",
    )
    return AWAITING_PROGRAM


async def receive_program(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle program input."""
    context.user_data["program"] = update.message.text
    
    await update.message.reply_text(
        f"✅ Program: {update.message.text}\n\n"
        f"📝 *Step 4/4: About You*\n\n"
        f"Write a short bio about yourself:",
        parse_mode="Markdown",
    )
    return AWAITING_BIO


async def receive_bio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle bio input and save the complete profile."""
    user = update.effective_user
    bio = update.message.text
    
    # Save profile to database
    await db.save_profile(
        telegram_id=user.id,
        university=context.user_data.get("university"),
        program=context.user_data.get("program"),
        bio=bio,
    )
    
    # Save photos
    photos = context.user_data.get("photos", [])
    if photos:
        await db.save_photos(user.id, photos)
    
    # Clear user data
    context.user_data.clear()
    
    await update.message.reply_text(
        "🎉 *Profile Complete!*\n\n"
        "Your profile has been saved successfully!\n\n"
        "You can now view or edit your profile from the home menu.",
        reply_markup=get_homepage_keyboard(True),
        parse_mode="Markdown",
    )
    return HOMEPAGE


# Edit handlers
async def edit_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle edit menu button presses."""
    text = update.message.text
    
    if text == BTN_EDIT_PHOTOS:
        context.user_data["photos"] = []
        await update.message.reply_text(
            f"📷 *Edit Photos*\n\n"
            f"Upload up to {MAX_PHOTOS} new photos.\n"
            f"This will replace your current photos.\n\n"
            f"Photos uploaded: 0/{MAX_PHOTOS}",
            reply_markup=get_photo_upload_keyboard(),
            parse_mode="Markdown",
        )
        return EDIT_PHOTOS
    
    elif text == BTN_EDIT_UNIVERSITY:
        profile = await db.get_profile(update.effective_user.id)
        current = profile["university"] if profile else "Not set"
        await update.message.reply_text(
            f"🏫 *Edit University*\n\n"
            f"Current: {current}\n\n"
            f"Enter your new university:",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="Markdown",
        )
        return EDIT_UNIVERSITY
    
    elif text == BTN_EDIT_PROGRAM:
        profile = await db.get_profile(update.effective_user.id)
        current = profile["program"] if profile else "Not set"
        await update.message.reply_text(
            f"📚 *Edit Program*\n\n"
            f"Current: {current}\n\n"
            f"Enter your new program:",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="Markdown",
        )
        return EDIT_PROGRAM
    
    elif text == BTN_EDIT_BIO:
        profile = await db.get_profile(update.effective_user.id)
        current = profile["bio"] if profile else "Not set"
        await update.message.reply_text(
            f"📝 *Edit Bio*\n\n"
            f"Current: {current}\n\n"
            f"Enter your new bio:",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="Markdown",
        )
        return EDIT_BIO
    
    elif text == BTN_BACK_HOME:
        has_profile = await db.profile_exists(update.effective_user.id)
        await update.message.reply_text(
            "🏠 *Home*\n\nWhat would you like to do?",
            reply_markup=get_homepage_keyboard(has_profile),
            parse_mode="Markdown",
        )
        return HOMEPAGE
    
    # Unknown input
    await update.message.reply_text(
        "Please use the buttons below.",
        reply_markup=get_edit_menu_keyboard(),
    )
    return EDIT_MENU


async def edit_photos_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle photo uploads during editing."""
    photos = context.user_data.get("photos", [])
    
    if len(photos) >= MAX_PHOTOS:
        await update.message.reply_text(
            f"❌ You've already uploaded {MAX_PHOTOS} photos. Tap 'Done' to save.",
            reply_markup=get_photo_upload_keyboard(),
        )
        return EDIT_PHOTOS
    
    photo = update.message.photo[-1]
    photos.append(photo.file_id)
    context.user_data["photos"] = photos
    
    remaining = MAX_PHOTOS - len(photos)
    
    await update.message.reply_text(
        f"📷 Photo {len(photos)}/{MAX_PHOTOS} received!\n"
        f"{'Upload more or tap Done.' if remaining > 0 else 'Tap Done to save.'}",
        reply_markup=get_photo_upload_keyboard(),
    )
    return EDIT_PHOTOS


async def edit_photos_done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle 'Done' button for photo editing."""
    user = update.effective_user
    photos = context.user_data.get("photos", [])
    
    if photos:
        await db.save_photos(user.id, photos)
    
    context.user_data.clear()
    
    await update.message.reply_text(
        f"✅ Photos updated! ({len(photos)} photo(s))\n\n"
        "What else would you like to edit?",
        reply_markup=get_edit_menu_keyboard(),
        parse_mode="Markdown",
    )
    return EDIT_MENU


async def edit_university_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle university editing."""
    await db.save_profile(update.effective_user.id, university=update.message.text)
    
    await update.message.reply_text(
        f"✅ University updated to: {update.message.text}\n\n"
        "What else would you like to edit?",
        reply_markup=get_edit_menu_keyboard(),
    )
    return EDIT_MENU


async def edit_program_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle program editing."""
    await db.save_profile(update.effective_user.id, program=update.message.text)
    
    await update.message.reply_text(
        f"✅ Program updated to: {update.message.text}\n\n"
        "What else would you like to edit?",
        reply_markup=get_edit_menu_keyboard(),
    )
    return EDIT_MENU


async def edit_bio_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle bio editing."""
    await db.save_profile(update.effective_user.id, bio=update.message.text)
    
    await update.message.reply_text(
        "✅ Bio updated!\n\n"
        "What else would you like to edit?",
        reply_markup=get_edit_menu_keyboard(),
    )
    return EDIT_MENU


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    help_text = (
        "🎓 *Student Meetup Bot Help*\n\n"
        "This bot helps you connect with fellow students from your university.\n\n"
        "*Commands:*\n"
        "/start - Go to homepage\n"
        "/help - Show this help message\n\n"
        "*Profile:*\n"
        "• Upload up to 3 photos\n"
        "• Add your university\n"
        "• Add your program/major\n"
        "• Write a bio about yourself\n\n"
        "Use the buttons to navigate!"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel and return to homepage."""
    context.user_data.clear()
    has_profile = await db.profile_exists(update.effective_user.id)
    
    await update.message.reply_text(
        "❌ Cancelled. Returning to home.",
        reply_markup=get_homepage_keyboard(has_profile),
    )
    return HOMEPAGE


def main() -> None:
    """Start the bot."""
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set!")
        return
    
    # Database initialization callback (runs in the bot's event loop)
    async def post_init(application):
        await db.init_db()
        logger.info("Database initialized")
    
    # Create application with post_init hook
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    
    # Create conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            HOMEPAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, homepage_handler),
            ],
            AWAITING_PHOTOS: [
                MessageHandler(filters.PHOTO, receive_photo),
                MessageHandler(filters.Regex(f"^{BTN_DONE_PHOTOS}$"), done_photos),
            ],
            AWAITING_UNIVERSITY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_university),
            ],
            AWAITING_PROGRAM: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_program),
            ],
            AWAITING_BIO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_bio),
            ],
            EDIT_MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_menu_handler),
            ],
            EDIT_PHOTOS: [
                MessageHandler(filters.PHOTO, edit_photos_receive),
                MessageHandler(filters.Regex(f"^{BTN_DONE_PHOTOS}$"), edit_photos_done),
            ],
            EDIT_UNIVERSITY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_university_receive),
            ],
            EDIT_PROGRAM: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_program_receive),
            ],
            EDIT_BIO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_bio_receive),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("start", start)],
    )
    
    # Add handlers
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("help", help_command))
    
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
        application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
