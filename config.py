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
# Requires DATABASE_URL environment variable (e.g., from AWS RDS)
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL environment variable is required!\n"
        "Please set it to your PostgreSQL connection string, e.g.:\n"
        "postgresql://user:password@host:port/database"
    )
if DATABASE_URL.startswith("postgres://"):
    # Fix for SQLAlchemy requiring postgresql:// scheme
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    # Ensure usage of asyncpg driver
    if "+asyncpg" not in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Maximum number of photos allowed per user
MAX_PHOTOS = 3
