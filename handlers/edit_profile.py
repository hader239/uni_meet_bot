"""Profile editing handlers."""

from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes

import database as db
from constants import (
    HOMEPAGE, EDIT_MENU, EDIT_PHOTOS, EDIT_UNIVERSITY, EDIT_PROGRAM, EDIT_BIO,
    BTN_EDIT_PHOTOS, BTN_EDIT_UNIVERSITY, BTN_EDIT_PROGRAM, BTN_EDIT_BIO, BTN_BACK_HOME,
    BTN_CANCEL_EDITING,
)
from keyboards import get_homepage_keyboard, get_edit_menu_keyboard, get_photo_upload_keyboard, get_text_edit_keyboard
from config import MAX_PHOTOS


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
            reply_markup=get_text_edit_keyboard(),
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
            reply_markup=get_text_edit_keyboard(),
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
            reply_markup=get_text_edit_keyboard(),
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


async def edit_photos_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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


async def edit_photos_done_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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


async def edit_university_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle university editing."""
    await db.save_profile(update.effective_user.id, university=update.message.text)
    
    await update.message.reply_text(
        f"✅ University updated to: {update.message.text}\n\n"
        "What else would you like to edit?",
        reply_markup=get_edit_menu_keyboard(),
    )
    return EDIT_MENU


async def edit_program_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle program editing."""
    await db.save_profile(update.effective_user.id, program=update.message.text)
    
    await update.message.reply_text(
        f"✅ Program updated to: {update.message.text}\n\n"
        "What else would you like to edit?",
        reply_markup=get_edit_menu_keyboard(),
    )
    return EDIT_MENU


async def edit_bio_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle bio editing."""
    await db.save_profile(update.effective_user.id, bio=update.message.text)
    
    await update.message.reply_text(
        "✅ Bio updated!\n\n"
        "What else would you like to edit?",
        reply_markup=get_edit_menu_keyboard(),
    )
    return EDIT_MENU


async def cancel_editing_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle cancel button during editing - return to edit menu without saving."""
    context.user_data.clear()
    
    await update.message.reply_text(
        "❌ Cancelled. No changes saved.\n\n"
        "What would you like to edit?",
        reply_markup=get_edit_menu_keyboard(),
    )
    return EDIT_MENU
