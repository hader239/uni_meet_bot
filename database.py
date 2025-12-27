"""Database operations for the Student Meetup Bot using SQLite."""

import aiosqlite
from datetime import datetime
from config import DATABASE_PATH


async def init_db():
    """Initialize the database and create tables if they don't exist."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Create users table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                university TEXT,
                program TEXT,
                bio TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create photos table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                file_id TEXT NOT NULL,
                position INTEGER NOT NULL,
                FOREIGN KEY (telegram_id) REFERENCES users (telegram_id),
                UNIQUE (telegram_id, position)
            )
        """)
        
        await db.commit()


async def get_profile(telegram_id: int) -> dict | None:
    """Get a user's profile by their Telegram ID."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # Get user data
        async with db.execute(
            "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
        ) as cursor:
            user_row = await cursor.fetchone()
        
        if not user_row:
            return None
        
        # Get photos
        async with db.execute(
            "SELECT file_id, position FROM photos WHERE telegram_id = ? ORDER BY position",
            (telegram_id,)
        ) as cursor:
            photo_rows = await cursor.fetchall()
        
        return {
            "telegram_id": user_row["telegram_id"],
            "university": user_row["university"],
            "program": user_row["program"],
            "bio": user_row["bio"],
            "photos": [row["file_id"] for row in photo_rows],
            "created_at": user_row["created_at"],
            "updated_at": user_row["updated_at"],
        }


async def save_profile(
    telegram_id: int,
    university: str | None = None,
    program: str | None = None,
    bio: str | None = None,
):
    """Save or update a user's profile."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Check if user exists
        async with db.execute(
            "SELECT id FROM users WHERE telegram_id = ?", (telegram_id,)
        ) as cursor:
            exists = await cursor.fetchone()
        
        if exists:
            # Update existing user - only update non-None fields
            updates = []
            params = []
            
            if university is not None:
                updates.append("university = ?")
                params.append(university)
            if program is not None:
                updates.append("program = ?")
                params.append(program)
            if bio is not None:
                updates.append("bio = ?")
                params.append(bio)
            
            if updates:
                updates.append("updated_at = ?")
                params.append(datetime.now().isoformat())
                params.append(telegram_id)
                
                query = f"UPDATE users SET {', '.join(updates)} WHERE telegram_id = ?"
                await db.execute(query, params)
        else:
            # Insert new user
            await db.execute(
                """
                INSERT INTO users (telegram_id, university, program, bio)
                VALUES (?, ?, ?, ?)
                """,
                (telegram_id, university, program, bio),
            )
        
        await db.commit()


async def save_photos(telegram_id: int, photo_file_ids: list[str]):
    """Save photos for a user, replacing any existing photos."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Delete existing photos
        await db.execute("DELETE FROM photos WHERE telegram_id = ?", (telegram_id,))
        
        # Insert new photos
        for position, file_id in enumerate(photo_file_ids, start=1):
            await db.execute(
                "INSERT INTO photos (telegram_id, file_id, position) VALUES (?, ?, ?)",
                (telegram_id, file_id, position),
            )
        
        await db.commit()


async def profile_exists(telegram_id: int) -> bool:
    """Check if a user has a profile."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT id FROM users WHERE telegram_id = ?", (telegram_id,)
        ) as cursor:
            return await cursor.fetchone() is not None
