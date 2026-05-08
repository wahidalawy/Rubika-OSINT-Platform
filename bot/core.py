import asyncio
import json
import re
from bot.logger import logger
from bot.client import RubikaClient
from bot.database import db

class RubikaEngine:
    def __init__(self):
        self.client = RubikaClient()
        self.offset = None
        self.is_running = False

    async def process_update(self, update: dict):
        msg = update.get("new_message", {})
        msg_id = msg.get("message_id")
        
        # --- Redis Deduplication ---
        if not msg_id or await db.is_message_processed(msg_id):
            return
            
        chat_id = update.get("chat_id", "")
        # Safe text extraction (prevents crash on photo-only messages)
        text = msg.get("text") or ""
        
        # --- The b0 Fix: Allow Bot PV chats and User chats ---
        if not (chat_id.startswith("u0") or chat_id.startswith("b0")):
            return

        logger.info("Processing user payload", extra={"extra_context": {"chat_id": chat_id, "msg_id": msg_id}})

        # 1. Start Command
        if text.strip() in ["/start", "استارت", "شروع", "help"]:
            welcome_text = (
                "به ربات استخراج آیدی کانال خوش آمدید 🌹\n"
                "مثل نور اما کوه ⛰️\n\n"
                "📌 دستورالعمل استفاده:\n"
                "کافیه یک پیام از کانال مورد نظرتون رو برای من **فوروارد (هدایت)** کنید تا آیدی سیستمیش رو بهتون بدم."
            )
            await self.client.send_message(chat_id, welcome_text, reply_to_message_id=msg_id)
            return

        # 2. Extraction Logic
        raw_json = json.dumps(update)
        channel_ids = list(set(re.findall(r"(c0[a-zA-Z0-9]{30})", raw_json)))
        
        if channel_ids:
            extracted_id = channel_ids[0]
            
            # --- Save to PostgreSQL ---
            await db.save_channel(extracted_id, chat_id)
            
            reply_text = f"🎉 آیدی کانال استخراج و در دیتابیس ثبت شد:\n\n🔴 `{extracted_id}`"
            await self.client.send_message(chat_id, reply_text, reply_to_message_id=msg_id)
            logger.info("Channel extracted & saved", extra={"extra_context": {"extracted_id": extracted_id}})
        else:
            error_text = "⚠️ آیدی کانالی پیدا نشد. مطمئنید پیام را مستقیماً از یک کانال پابلیک فوروارد کردید؟"
            await self.client.send_message(chat_id, error_text, reply_to_message_id=msg_id)

    async def start_polling(self):
        self.is_running = True
        logger.info("🚀 Core Engine async polling started...")
        
        while self.is_running:
            try:
                data = await self.client.get_updates(offset=self.offset)
                if data and data.get("status") == "OK":
                    data_block = data.get("data", {})
                    
                    # --- The Time Loop Fix: next_offset_id ---
                    if "next_offset_id" in data_block and data_block["next_offset_id"]:
                        self.offset = data_block["next_offset_id"]

                    for update in data_block.get("updates", []):
                        asyncio.create_task(self.process_update(update))
                        
            except Exception as e:
                logger.error(f"Critical Polling Error: {str(e)}", exc_info=True)
            await asyncio.sleep(2)

    async def stop(self):
        self.is_running = False
        await self.client.close()