"""Profile browsing/discovery handlers."""

from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes

import database as db
from constants import HOMEPAGE, BROWSING, BTN_LIKE, BTN_PASS, BTN_STOP_BROWSING
from keyboards import get_homepage_keyboard, get_browse_keyboard


async def show_next_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show the next profile to the user."""
    user = update.effective_user
    profile = await db.get_next_profile(user.id)
    
    if not profile:
        await update.message.reply_text(
            "😔 *No more profiles to show!*\n\n"
            "Check back later for new users.",
            reply_markup=get_homepage_keyboard(True),
            parse_mode="Markdown",
        )
        return HOMEPAGE
    
    # Store current profile being viewed
    context.user_data["viewing_profile"] = profile["telegram_id"]
    
    # Format profile text
    profile_text = (
        f"🏫 *University:* {profile['university'] or 'Not set'}\n"
        f"📚 *Program:* {profile['program'] or 'Not set'}\n"
        f"📝 *About:* {profile['bio'] or 'Not set'}"
    )
    
    # Send profile with photos if available
    if profile["photos"]:
        if len(profile["photos"]) == 1:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=profile["photos"][0],
                caption=profile_text,
                parse_mode="Markdown",
                reply_markup=get_browse_keyboard(),
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
                "👆 What do you think?",
                reply_markup=get_browse_keyboard(),
            )
    else:
        await update.message.reply_text(
            profile_text + "\n📷 *Photos:* None",
            reply_markup=get_browse_keyboard(),
            parse_mode="Markdown",
        )
    
    return BROWSING


async def start_browsing_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start browsing profiles."""
    return await show_next_profile(update, context)


async def like_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle like action."""
    user = update.effective_user
    target_id = context.user_data.get("viewing_profile")
    
    if target_id:
        await db.record_interaction(user.id, target_id, is_like=True)
        
        # Check for mutual like
        if await db.check_mutual_like(user.id, target_id):
            await update.message.reply_text(
                "🎉 *It's a match!*\n\n"
                "You both liked each other!",
                parse_mode="Markdown",
            )
    
    return await show_next_profile(update, context)


async def pass_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle pass action."""
    user = update.effective_user
    target_id = context.user_data.get("viewing_profile")
    
    if target_id:
        await db.record_interaction(user.id, target_id, is_like=False)
    
    return await show_next_profile(update, context)


async def stop_browsing_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stop browsing and return to homepage."""
    context.user_data.pop("viewing_profile", None)
    
    await update.message.reply_text(
        "🏠 *Home*\n\nWhat would you like to do?",
        reply_markup=get_homepage_keyboard(True),
        parse_mode="Markdown",
    )
    return HOMEPAGE
