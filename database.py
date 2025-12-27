"""Database operations for the Student Meetup Bot using SQLAlchemy."""

from datetime import datetime
from sqlalchemy import (
    MetaData, Table, Column, Integer, BigInteger, String, DateTime, ForeignKey, 
    UniqueConstraint, select, update, delete, insert
)
from sqlalchemy.ext.asyncio import create_async_engine
from config import DATABASE_URL

# SQLAlchemy Setup
metadata = MetaData()

# Define Tables
users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("telegram_id", BigInteger, unique=True, nullable=False),
    Column("university", String),
    Column("program", String),
    Column("bio", String),
    Column("created_at", DateTime, default=datetime.now),
    Column("updated_at", DateTime, default=datetime.now, onupdate=datetime.now),
)

photos = Table(
    "photos",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("telegram_id", BigInteger, ForeignKey("users.telegram_id"), nullable=False),
    Column("file_id", String, nullable=False),
    Column("position", Integer, nullable=False),
    UniqueConstraint("telegram_id", "position", name="uq_user_photo_position"),
)

# Create Async Engine
engine = create_async_engine(DATABASE_URL, echo=False)


async def init_db():
    """Initialize the database and create tables if they don't exist."""
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)


async def get_profile(telegram_id: int) -> dict | None:
    """Get a user's profile by their Telegram ID."""
    async with engine.connect() as conn:
        # Get user data
        stmt = select(users).where(users.c.telegram_id == telegram_id)
        result = await conn.execute(stmt)
        user_row = result.fetchone()

        if not user_row:
            return None

        # Get photos
        stmt_photos = (
            select(photos.c.file_id)
            .where(photos.c.telegram_id == telegram_id)
            .order_by(photos.c.position)
        )
        result_photos = await conn.execute(stmt_photos)
        photo_file_ids = [row[0] for row in result_photos.fetchall()]

        return {
            "telegram_id": user_row.telegram_id,
            "university": user_row.university,
            "program": user_row.program,
            "bio": user_row.bio,
            "photos": photo_file_ids,
            "created_at": user_row.created_at,
            "updated_at": user_row.updated_at,
        }


async def save_profile(
    telegram_id: int,
    university: str | None = None,
    program: str | None = None,
    bio: str | None = None,
):
    """Save or update a user's profile."""
    # Build values dictionary with only non-None values
    values = {}
    if university is not None:
        values["university"] = university
    if program is not None:
        values["program"] = program
    if bio is not None:
        values["bio"] = bio


    async with engine.begin() as conn:
        # Check if user exists
        stmt_check = select(users.c.id).where(users.c.telegram_id == telegram_id)
        result = await conn.execute(stmt_check)
        exists = result.scalar_one_or_none()

        if exists:
            if values:
                values["updated_at"] = datetime.now()
                stmt_update = (
                    update(users)
                    .where(users.c.telegram_id == telegram_id)
                    .values(**values)
                )
                await conn.execute(stmt_update)
        else:
            # Insert new user
            # Ensure we insert required fields even if None (though schema allows nulls mostly)
            # But telegram_id is required.
            insert_values = {
                "telegram_id": telegram_id,
                "university": university,
                "program": program,
                "bio": bio
            }
            stmt_insert = insert(users).values(**insert_values)
            await conn.execute(stmt_insert)


async def save_photos(telegram_id: int, photo_file_ids: list[str]):
    """Save photos for a user, replacing any existing photos."""
    async with engine.begin() as conn:
        # Delete existing photos
        stmt_delete = delete(photos).where(photos.c.telegram_id == telegram_id)
        await conn.execute(stmt_delete)

        # Insert new photos
        if photo_file_ids:
            values_list = [
                {
                    "telegram_id": telegram_id,
                    "file_id": file_id,
                    "position": i
                }
                for i, file_id in enumerate(photo_file_ids, start=1)
            ]
            stmt_insert = insert(photos).values(values_list)
            await conn.execute(stmt_insert)


async def profile_exists(telegram_id: int) -> bool:
    """Check if a user has a profile."""
    async with engine.connect() as conn:
        stmt = select(users.c.id).where(users.c.telegram_id == telegram_id)
        result = await conn.execute(stmt)
        return result.scalar_one_or_none() is not None
