"""Database operations for the Student Meetup Bot using SQLAlchemy."""

from datetime import datetime
from sqlalchemy import (
    MetaData, Table, Column, BigInteger, Text, DateTime,
    select, update, insert, ARRAY, inspect
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from config import DATABASE_URL

# SQLAlchemy Setup
metadata = MetaData()

# Single users table with photos as array
users = Table(
    "users",
    metadata,
    Column("telegram_id", BigInteger, primary_key=True),
    Column("university", Text),
    Column("program", Text),
    Column("bio", Text),
    Column("photos", ARRAY(Text)),  # Array of photo file_ids
    Column("created_at", DateTime, default=datetime.now),
    Column("updated_at", DateTime, default=datetime.now, onupdate=datetime.now),
)

# Lazy engine initialization to avoid event loop issues
_engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    """Get or create the async engine (lazy initialization)."""
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            DATABASE_URL,
            echo=False,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
        )
    return _engine


async def init_db() -> bool:
    """Initialize the database and create tables if they don't exist.
    
    Returns:
        True if tables were created, False if they already existed.
    """
    engine = get_engine()
    async with engine.begin() as conn:
        # Check if table exists before creating
        tables_before = await conn.run_sync(
            lambda sync_conn: inspect(sync_conn).get_table_names()
        )
        existed = "users" in tables_before
        
        # create_all is idempotent - only creates if not exists
        await conn.run_sync(metadata.create_all)
        
        return not existed


async def get_profile(telegram_id: int) -> dict | None:
    """Get a user's profile by their Telegram ID."""
    engine = get_engine()
    async with engine.connect() as conn:
        stmt = select(users).where(users.c.telegram_id == telegram_id)
        result = await conn.execute(stmt)
        user_row = result.fetchone()

        if not user_row:
            return None

        return {
            "telegram_id": user_row.telegram_id,
            "university": user_row.university,
            "program": user_row.program,
            "bio": user_row.bio,
            "photos": user_row.photos or [],  # Return empty list if None
            "created_at": user_row.created_at,
            "updated_at": user_row.updated_at,
        }


async def save_profile(
    telegram_id: int,
    university: str | None = None,
    program: str | None = None,
    bio: str | None = None,
    photos: list[str] | None = None,
):
    """Save or update a user's profile."""
    engine = get_engine()
    values = {}
    if university is not None:
        values["university"] = university
    if program is not None:
        values["program"] = program
    if bio is not None:
        values["bio"] = bio
    if photos is not None:
        values["photos"] = photos

    async with engine.begin() as conn:
        # Check if user exists
        stmt_check = select(users.c.telegram_id).where(users.c.telegram_id == telegram_id)
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
            insert_values = {
                "telegram_id": telegram_id,
                "university": university,
                "program": program,
                "bio": bio,
                "photos": photos or [],
            }
            stmt_insert = insert(users).values(**insert_values)
            await conn.execute(stmt_insert)


async def save_photos(telegram_id: int, photo_file_ids: list[str]):
    """Save photos for a user (convenience function)."""
    await save_profile(telegram_id, photos=photo_file_ids)


async def profile_exists(telegram_id: int) -> bool:
    """Check if a user has a profile."""
    engine = get_engine()
    async with engine.connect() as conn:
        stmt = select(users.c.telegram_id).where(users.c.telegram_id == telegram_id)
        result = await conn.execute(stmt)
        return result.scalar_one_or_none() is not None
