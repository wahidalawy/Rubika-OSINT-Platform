import aiohttp
import asyncio
from config.settings import settings
from bot.logger import logger

class RubikaClient:
    """Enterprise-grade async HTTP client for the Rubika Bot API."""
    def __init__(self):
        self.base_url = settings.API_BASE_URL
        self.token = settings.BOT_TOKEN
        self.session = None

    async def get_session(self):
        """Lazy initialization of the aiohttp session with strict timeouts."""
        if self.session is None or self.session.closed:
            # 15 seconds max connection time to prevent hanging
            timeout = aiohttp.ClientTimeout(total=15)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session

    async def _make_request(self, method: str, payload: dict, retries: int = 3) -> dict:
        """Centralized request handler with retry logic for 5xx errors."""
        url = f"{self.base_url}/{self.token}/{method}"
        session = await self.get_session()
        
        for attempt in range(retries):
            try:
                async with session.post(url, json=payload) as response:
                    # اگر خطای سروری (502, 503, 504) گرفتیم، تلاش مجدد کنیم
                    if response.status in [502, 503, 504]:
                        wait_time = (attempt + 1) * 2
                        logger.warning(f"Server Error {response.status}. Retrying in {wait_time}s... (Attempt {attempt+1}/{retries})")
                        await asyncio.sleep(wait_time)
                        continue
                        
                    response.raise_for_status()
                    return await response.json()
            except asyncio.TimeoutError:
                logger.warning(f"API Timeout during {method}. Attempt {attempt+1}/{retries}")
                await asyncio.sleep(2)
            except Exception as e:
                # اگر در تلاش آخر بودیم، خطا را لاگ کنیم
                if attempt == retries - 1:
                    logger.error(f"Final API Error during {method}: {str(e)}", exc_info=True)
                await asyncio.sleep(1)
        
        return None

    async def get_updates(self, offset: str = None, limit: int = 20) -> dict:
        payload = {"limit": limit}
        if offset:
            payload["offset"] = offset
        return await self._make_request("getUpdates", payload)

    async def send_message(self, chat_id: str, text: str, reply_to_message_id: str = None) -> dict:
        payload = {"chat_id": chat_id, "text": text}
        if reply_to_message_id:
            payload["reply_to_message_id"] = reply_to_message_id
        return await self._make_request("sendMessage", payload)
        
    async def close(self):
        """Gracefully close the network session."""
        if self.session and not self.session.closed:
            await self.session.close()