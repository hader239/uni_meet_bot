"""Keyboard definitions for the Student Meetup Bot."""

from telegram import ReplyKeyboardMarkup
from constants import (
    BTN_FILL_PROFILE, BTN_EDIT_PROFILE, BTN_VIEW_PROFILE, BTN_SEARCH,
    BTN_BACK_HOME, BTN_DONE_PHOTOS, BTN_CANCEL_EDITING,
    BTN_EDIT_PHOTOS, BTN_EDIT_UNIVERSITY, BTN_EDIT_PROGRAM, BTN_EDIT_BIO,
    BTN_LIKE, BTN_PASS, BTN_STOP_BROWSING,
)


def get_homepage_keyboard(has_profile: bool = False) -> ReplyKeyboardMarkup:
    """Get the homepage keyboard based on whether user has a profile."""
    if has_profile:
        keyboard = [
            [BTN_SEARCH],
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
        [BTN_CANCEL_EDITING],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_text_edit_keyboard() -> ReplyKeyboardMarkup:
    """Get the keyboard for text editing states (university, program, bio)."""
    keyboard = [
        [BTN_CANCEL_EDITING],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_browse_keyboard() -> ReplyKeyboardMarkup:
    """Get the keyboard for browsing profiles."""
    keyboard = [
        [BTN_LIKE, BTN_PASS],
        [BTN_STOP_BROWSING],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
