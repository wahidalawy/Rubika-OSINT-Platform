import asyncio
import json
import re
from bot.logger import logger
from bot.client import RubikaClient

class RubikaEngine:
    """Core orchestration engine managing the event loop and data extraction."""
    def __init__(self):
        self.client = RubikaClient()
        self.offset = None
        self.seen_messages = set() # Temporary state (will be replaced by Redis in Phase 3)
        self.is_running = False

    async def process_update(self, update: dict):
        """Processes a single update concurrently."""
        msg = update.get("new_message", {})
        msg_id = msg.get("message_id")
        
        # Deduplication check
        if not msg_id or msg_id in self.seen_messages:
            return
            
        self.seen_messages.add(msg_id)
        chat_id = update.get("chat_id", "")
        text = msg.get("text", "")
        
        # Strict isolation: Ignore Channels (c0) and Groups (g0). Only process Users (u0).
        if not chat_id.startswith("u0"):
            return

        logger.info("Processing user payload", extra={"extra_context": {"user_id": chat_id, "msg_id": msg_id}})

        # 1. Onboarding workflow
        if text.strip() in ["/start", "استارت", "شروع"]:
            welcome_text = (
                "سلام! 👋\n"
                "به ربات استخراج آیدی روبیکا خوش آمدید.\n\n"
                "📌 برای پیدا کردن آیدی، کافیه یک پیام از کانال مورد نظرتون رو برای من **فوروارد (هدایت)** کنید.\n"
                "نیاز نیست من ادمین اون کانال باشم! 😉"
            )
            await self.client.send_message(chat_id, welcome_text, reply_to_message_id=msg_id)
            logger.info("Onboarding workflow executed", extra={"extra_context": {"user_id": chat_id}})
            return

        # 2. Metadata Extraction workflow
        raw_json = json.dumps(update)
        
        # Regex extraction: Look for any string starting with c0 followed by exactly 30 alphanumeric characters
        channel_ids = list(set(re.findall(r"(c0[a-zA-Z0-9]{30})", raw_json)))
        
        if channel_ids:
            extracted_id = channel_ids[0]
            reply_text = (
                "🎉 آیدی کانال با موفقیت استخراج شد:\n\n"
                f"🔴 `{extracted_id}`\n\n"
                "✅ می‌تونید این آیدی رو کپی کنید."
            )
            await self.client.send_message(chat_id, reply_text, reply_to_message_id=msg_id)
            logger.info("Metadata extraction successful", extra={"extra_context": {"user_id": chat_id, "extracted_id": extracted_id}})
        else:
            error_text = "⚠️ من در این پیام آیدی کانالی پیدا نکردم.\nلطفاً حتماً یک پیام را مستقیماً از داخل یک کانال به اینجا **فوروارد** کنید."
            await self.client.send_message(chat_id, error_text, reply_to_message_id=msg_id)
            logger.warning("Extraction failed - No ID present", extra={"extra_context": {"user_id": chat_id, "reason": "No c0 regex match"}})

    async def start_polling(self):
        """The main non-blocking polling loop."""
        self.is_running = True
        logger.info("🚀 Core Engine async polling started...", extra={"extra_context": {"status": "running"}})
        
        while self.is_running:
            try:
                data = await self.client.get_updates(offset=self.offset)
                
                if data and data.get("status") == "OK":
                    data_block = data.get("data", {})
                    updates = data_block.get("updates", [])
                    
                    if "next_offset" in data_block and data_block["next_offset"]:
                        self.offset = data_block["next_offset"]

                    for update in updates:
                        # Schedule the update processing as a parallel background task
                        asyncio.create_task(self.process_update(update))
                        
                elif data:
                    logger.warning(f"Unexpected API response payload: {data}")
                    
            except Exception as e:
                logger.error(f"Critical Polling Error: {str(e)}", exc_info=True)
            
            await asyncio.sleep(2) # Backoff to prevent rate-limits

    async def stop(self):
        """Graceful shutdown hook."""
        self.is_running = False
        await self.client.close()
        logger.info("Engine gracefully shut down.", extra={"extra_context": {"status": "stopped"}})