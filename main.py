import asyncio
from config.settings import settings
from bot.logger import logger
from bot.core import RubikaEngine
from bot.database import db

async def async_main():
    engine = RubikaEngine()
    try:
        settings.validate()
        logger.info("System starting up...")
        
        # --- CONNECT TO DATABASES ---
        await db.connect()
        
        # Start the asynchronous engine
        await engine.start_polling()
        
    except asyncio.CancelledError:
        logger.info("Asyncio task cancelled. Shutting down...")
    except KeyboardInterrupt:
        logger.info("Received hardware interrupt (Ctrl+C). Initiating graceful shutdown...")
    except Exception as e:
        logger.critical(f"Fatal Startup Error: {str(e)}", exc_info=True)
    finally:
        await engine.stop()
        # --- DISCONNECT FROM DATABASES ---
        await db.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        pass