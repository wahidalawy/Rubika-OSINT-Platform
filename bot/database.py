import asyncpg
import redis.asyncio as aioredis
import os
from bot.logger import logger

class DatabaseManager:
    """Enterprise Database & Cache connection manager."""
    def __init__(self):
        self.pg_pool = None
        self.redis = None

    async def connect(self):
        # 1. Connect to PostgreSQL
        try:
            db_url = os.getenv("DATABASE_URL")
            self.pg_pool = await asyncpg.create_pool(db_url)
            
            # Auto-migrate: Create table if it doesn't exist
            async with self.pg_pool.acquire() as conn:
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS extracted_channels (
                        id SERIAL PRIMARY KEY,
                        channel_id VARCHAR(50) UNIQUE NOT NULL,
                        extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        extracted_by_user VARCHAR(50)
                    )
                ''')
            logger.info("PostgreSQL connection pool established and schema verified.")
        except Exception as e:
            logger.critical(f"Failed to connect to PostgreSQL: {e}", exc_info=True)
            raise

        # 2. Connect to Redis
        try:
            redis_url = os.getenv("REDIS_URL")
            self.redis = await aioredis.from_url(redis_url, decode_responses=True)
            await self.redis.ping()
            logger.info("Redis cache connection established.")
        except Exception as e:
            logger.critical(f"Failed to connect to Redis: {e}", exc_info=True)
            raise

    async def save_channel(self, channel_id: str, user_id: str):
        """Save a newly discovered channel to PostgreSQL."""
        try:
            async with self.pg_pool.acquire() as conn:
                # INSERT ignores duplicates based on the UNIQUE constraint
                await conn.execute('''
                    INSERT INTO extracted_channels (channel_id, extracted_by_user)
                    VALUES ($1, $2)
                    ON CONFLICT (channel_id) DO NOTHING
                ''', channel_id, user_id)
        except Exception as e:
            logger.error(f"Database Insert Error: {e}")

    async def is_message_processed(self, message_id: str) -> bool:
        """Check Redis to prevent duplicate processing. Keeps memory clean via 24h TTL."""
        if not self.redis:
            return False
            
        # SETNX sets the key only if it doesn't exist. 
        # ex=86400 ensures the key deletes itself after 24 hours.
        is_new = await self.redis.set(f"msg:{message_id}", "1", nx=True, ex=86400)
        return not is_new # Returns True if it was ALREADY processed

    async def disconnect(self):
        if self.pg_pool:
            await self.pg_pool.close()
        if self.redis:
            await self.redis.close()
        logger.info("Database connections safely closed.")

# Export a single global instance
db = DatabaseManager()