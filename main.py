import asyncio
from config.settings import settings
from bot.logger import logger
from bot.core import RubikaEngine

async def async_main():
    engine = RubikaEngine()
    try:
        settings.validate()
        logger.info("System starting up...", extra={"extra_context": {"action": "startup_sequence", "status": "initializing"}})
        
        masked_token = f"***{settings.BOT_TOKEN[-5:]}"
        logger.info(f"Configuration loaded. Bot Token: {masked_token}")
        
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

if __name__ == "__main__":
    # Bootstrapping the asynchronous event loop
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        pass # Handle the terminal interrupt cleanly