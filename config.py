"""Configuration for the Telegram Student Meetup Bot."""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Bot token from environment variable
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# Webhook configuration (for Railway deployment)
# Railway provides PORT and RAILWAY_PUBLIC_DOMAIN automatically
PORT = int(os.environ.get("PORT", 8080))
WEBHOOK_URL = os.environ.get("RAILWAY_PUBLIC_DOMAIN")  # e.g., "your-app.up.railway.app"

# Database configuration
DATABASE_PATH = "student_meetup.db"

# Maximum number of photos allowed per user
MAX_PHOTOS = 3
