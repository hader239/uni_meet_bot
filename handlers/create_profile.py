"""Profile creation handlers."""

from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes

import database as db
from constants import HOMEPAGE, AWAITING_PHOTOS, AWAITING_UNIVERSITY, AWAITING_PROGRAM, AWAITING_BIO
from keyboards import get_homepage_keyboard, get_photo_upload_keyboard
from config import MAX_PHOTOS


async def receive_photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle photo uploads during profile creation."""
    photos = context.user_data.get("photos", [])
    
    if len(photos) >= MAX_PHOTOS:
        await update.message.reply_text(
            f"❌ You've already uploaded {MAX_PHOTOS} photos. "
            f"Tap 'Done' to continue.",
            reply_markup=get_photo_upload_keyboard(),
        )
        return AWAITING_PHOTOS
    
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


async def done_photos_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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


async def receive_university_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle university input."""
    context.user_data["university"] = update.message.text
    
    await update.message.reply_text(
        f"✅ University: {update.message.text}\n\n"
        f"📚 *Step 3/4: Program*\n\n"
        f"Please enter your program/major:",
        parse_mode="Markdown",
    )
    return AWAITING_PROGRAM


async def receive_program_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle program input."""
    context.user_data["program"] = update.message.text
    
    await update.message.reply_text(
        f"✅ Program: {update.message.text}\n\n"
        f"📝 *Step 4/4: About You*\n\n"
        f"Write a short bio about yourself:",
        parse_mode="Markdown",
    )
    return AWAITING_BIO


async def receive_bio_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle bio input and save the complete profile."""
    user = update.effective_user
    bio = update.message.text
    
    # Save profile with photos
    photos = context.user_data.get("photos", [])
    await db.save_profile(
        telegram_id=user.id,
        university=context.user_data.get("university"),
        program=context.user_data.get("program"),
        bio=bio,
        photos=photos,
    )
    
    context.user_data.clear()
    
    await update.message.reply_text(
        "🎉 *Profile Complete!*\n\n"
        "Your profile has been saved successfully!\n\n"
        "You can now view or edit your profile from the home menu.",
        reply_markup=get_homepage_keyboard(True),
        parse_mode="Markdown",
    )
    return HOMEPAGE
