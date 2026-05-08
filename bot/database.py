import asyncpg
import redis.asyncio as aioredis
import os
from bot.logger import logger

class DatabaseManager:
    def __init__(self):
        self.pg_pool = None
        self.redis = None

    async def connect(self):
        try:
            db_url = os.getenv("DATABASE_URL")
            self.pg_pool = await asyncpg.create_pool(db_url)
            
            # Auto-migrate: ساخت جدول جدید و جامع‌تر
            async with self.pg_pool.acquire() as conn:
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS extracted_entities (
                        id SERIAL PRIMARY KEY,
                        entity_id VARCHAR(50) UNIQUE NOT NULL,
                        entity_type VARCHAR(20),
                        extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        extracted_by_user VARCHAR(50)
                    )
                ''')
            logger.info("PostgreSQL connection pool established and schema verified.")
        except Exception as e:
            logger.critical(f"Failed to connect to PostgreSQL: {e}", exc_info=True)
            raise

        try:
            redis_url = os.getenv("REDIS_URL")
            self.redis = await aioredis.from_url(redis_url, decode_responses=True)
            await self.redis.ping()
            logger.info("Redis cache connection established.")
        except Exception as e:
            logger.critical(f"Failed to connect to Redis: {e}", exc_info=True)
            raise

    async def save_entity(self, entity_id: str, entity_type: str, user_id: str):
        """ذخیره آیدی استخراج شده همراه با نوع آن در دیتابیس"""
        try:
            async with self.pg_pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO extracted_entities (entity_id, entity_type, extracted_by_user)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (entity_id) DO NOTHING
                ''', entity_id, entity_type, user_id)
        except Exception as e:
            logger.error(f"Database Insert Error: {e}")

    async def is_message_processed(self, message_id: str) -> bool:
        if not self.redis: return False
        is_new = await self.redis.set(f"msg:{message_id}", "1", nx=True, ex=86400)
        return not is_new 

    async def disconnect(self):
        if self.pg_pool: await self.pg_pool.close()
        if self.redis: await self.redis.close()
        logger.info("Database connections safely closed.")

db = DatabaseManager()