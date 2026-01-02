"""Start and homepage handlers."""

from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes

import database as db
from constants import (
    HOMEPAGE, AWAITING_PHOTOS, EDIT_MENU, BROWSING,
    BTN_FILL_PROFILE, BTN_EDIT_PROFILE, BTN_VIEW_PROFILE, BTN_SEARCH,
)
from keyboards import get_homepage_keyboard, get_edit_menu_keyboard, get_photo_upload_keyboard
from config import MAX_PHOTOS
from handlers.browse import show_next_profile


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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
    
    elif text == BTN_SEARCH:
        return await show_next_profile(update, context)
    
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
    
    # Unknown input
    has_profile = await db.profile_exists(user.id)
    await update.message.reply_text(
        "Please use the buttons below.",
        reply_markup=get_homepage_keyboard(has_profile),
    )
    return HOMEPAGE


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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


async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel and return to homepage."""
    context.user_data.clear()
    has_profile = await db.profile_exists(update.effective_user.id)
    
    await update.message.reply_text(
        "❌ Cancelled. Returning to home.",
        reply_markup=get_homepage_keyboard(has_profile),
    )
    return HOMEPAGE
