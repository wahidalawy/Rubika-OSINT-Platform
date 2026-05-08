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

    def get_entity_info(self, entity_id: str):
        """تشخیص نوع آیدی بر اساس حروف شروع‌کننده"""
        if entity_id.startswith("c0"): return "کانال 📢", "Channel"
        if entity_id.startswith("u0"): return "کاربر 👤", "User"
        if entity_id.startswith("g0"): return "گروه 👥", "Group"
        return "ناشناخته ❓", "Unknown"

    async def process_update(self, update: dict):
        msg = update.get("new_message", {})
        msg_id = msg.get("message_id")
        
        if not msg_id or await db.is_message_processed(msg_id):
            return
            
        chat_id = update.get("chat_id", "")
        text = msg.get("text") or ""
        
        if not (chat_id.startswith("u0") or chat_id.startswith("b0")):
            return

        logger.info("Processing user payload", extra={"extra_context": {"chat_id": chat_id}})

        if text.strip() in ["/start", "استارت", "شروع", "help"]:
            welcome_text = (
                "به پلتفرم استخراج آیدی روبیکا خوش آمدید 🔍\n\n"
                "📌 امکانات ربات:\n"
                "• استخراج آیدی **کانال‌ها** (c0...)\n"
                "• استخراج آیدی **گروه‌ها** (g0...)\n"
                "• استخراج آیدی **کاربران** (u0...)\n\n"
                "کافیه یک پیام از شخص، گروه یا کانال مورد نظرتون رو برای من **فوروارد** کنید."
            )
            await self.client.send_message(chat_id, welcome_text, reply_to_message_id=msg_id)
            return

        raw_json = json.dumps(update)
        # Regex برای شکار هر رشته‌ای که با c0, u0 یا g0 شروع می‌شود و دقیقا ۳۰ کاراکتر دارد
        found_ids = list(set(re.findall(r"([cug]0[a-zA-Z0-9]{30})", raw_json)))
        
        # حذف آیدی خود فرستنده پیام از لیست استخراج (تا ربات آیدی خودمون رو برنگردونه)
        if chat_id in found_ids:
            found_ids.remove(chat_id)

        if found_ids:
            extracted_id = found_ids[0]
            fa_label, en_type = self.get_entity_info(extracted_id)
            
            await db.save_entity(extracted_id, en_type, chat_id)
            
            reply_text = f"🎉 آیدی {fa_label} با موفقیت استخراج شد:\n\n🔴 `{extracted_id}`"
            await self.client.send_message(chat_id, reply_text, reply_to_message_id=msg_id)
            logger.info(f"Entity extracted & saved: {en_type}", extra={"extra_context": {"extracted_id": extracted_id}})
        else:
            error_text = "⚠️ هیچ آیدی پنهانی در این پیام پیدا نشد. لطفاً پیام دیگری را مستقیماً فوروارد کنید."
            await self.client.send_message(chat_id, error_text, reply_to_message_id=msg_id)

    async def start_polling(self):
        self.is_running = True
        logger.info("🚀 Core Engine async polling started...")
        while self.is_running:
            try:
                data = await self.client.get_updates(offset=self.offset)
                if data and data.get("status") == "OK":
                    data_block = data.get("data", {})
                    if "next_offset_id" in data_block and data_block["next_offset_id"]:
                        self.offset = data_block["next_offset_id"]

                    for update in data_block.get("updates", []):
                        asyncio.create_task(self.process_update(update))
            except Exception as e:
                logger.error(f"Critical Polling Error: {str(e)}")
            await asyncio.sleep(2)

    async def stop(self):
        self.is_running = False
        await self.client.close()