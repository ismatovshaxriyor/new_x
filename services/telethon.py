import asyncio
import logging
from telethon.sync import TelegramClient
from telethon.tl.functions.payments import GetStarGiftsRequest
from telethon.errors import FloodWaitError, RPCError

from config import API_HASH, API_ID, PHONE_NUMBER
from database.models import Gift

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

CHECK_INTERVAL_SECONDS = 50
FLOOD_WAIT_MAX = 30


class TelegramGiftMonitor:
    def __init__(self, api_id, api_hash, phone_number, bot):
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone_number = phone_number
        self.client = None
        self.last_gifts_hash = 0 
        self.bot = bot 

    async def _connect(self):
        logger.info("🔌 Telegram userbot ulanishga harakat qilmoqda...")
        self.client = TelegramClient(
            'userbot_session',
            self.api_id,
            self.api_hash,
        )
        try:
            await self.client.start(phone=self.phone_number)
            logger.info("✅ Telegram userbot muvaffaqiyatli ulandi!")
        except Exception as e:
            logger.critical(f"🔴 Userbot ulanishda xato: {e}", exc_info=True)
            raise

    def _get_gift_attribute(self, gift_tl, attributes):
        for attr in attributes:
            if hasattr(gift_tl, attr):
                return getattr(gift_tl, attr)
        return None

    async def _get_gifts(self):
        logger.info("🔍 Yangi giftlar uchun Telegram API tekshirilmoqda...")
        try:
            gifts_response = await self.client(GetStarGiftsRequest(hash=self.last_gifts_hash))
            try:
                gifts = gifts_response.gifts
                logger.info("✅ Gifts ro'yxati muvaffaqiyatli olindi")
                
                if not gifts:
                    logger.info("ℹ️ Gift ro'yxati bo'sh - yangi giftlar yo'q")
                    return
                
                for gift_tl in gifts:
                    try:
                        gift_id = gift_tl.id
                        gift_obj = Gift.get_or_none(id=gift_id)
                        if gift_obj:
                            continue

                        logger.info(f'YANGI GIFT TOPILDI!!!  ID: {gift_id}')
                        stars = self._get_gift_attribute(gift_tl, ['stars'])
                        limited = self._get_gift_attribute(gift_tl, ['limited'])
                        sold_out = self._get_gift_attribute(gift_tl, ['sold_out'])
                        first_sale_date = self._get_gift_attribute(gift_tl, ['first_sale_date'])
                        last_sale_date = self._get_gift_attribute(gift_tl, ['last_sale_date'])

                        Gift.create(
                            id=gift_id,
                            stars=stars,
                            limited=limited,
                            sold_out=sold_out,
                            first_sale_date=first_sale_date,
                            last_sale_date=last_sale_date,
                        )

                    except Exception as gift_error:
                        logger.error(f"❌ Gift ({gift_tl}) ishlov berishda xato: {gift_error}", exc_info=True)

            except AttributeError as e:
                    logger.info(f"ℹ️ Javobda 'gifts' atributi yo'q - yangilanish yo'q yoki boshqa javob turi. Xato: {e}")
                    return

        except FloodWaitError as e:
            wait_time = min(e.seconds + 5, FLOOD_WAIT_MAX)
            logger.warning(f"⏳ FloodWaitError! {wait_time} soniya kutilmoqda. Xato: {e}")
            await asyncio.sleep(wait_time)
        except RPCError as e:
            logger.error(f"❌ Telethon RPC xatosi: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"❌ Kutilmagan xato: {e}", exc_info=True)


async def main_userbot(bot):
    if not all([API_ID, API_HASH, PHONE_NUMBER]):
        logger.critical("🔴 Muhit o'zgaruvchilari (API_ID, API_HASH, PHONE_NUMBER) to'liq emas. Iltimos, config.py faylini tekshiring.")
        return
    
    monitor = TelegramGiftMonitor(API_ID, API_HASH, PHONE_NUMBER, bot)
    
    try:
        await monitor._connect()
        logger.info(f"🚀 Userbot doimiy kuzatish rejimida ishga tushdi. Har {CHECK_INTERVAL_SECONDS} soniyada tekshiradi.")
        while True:
            try:
                await monitor._get_gifts()
                await asyncio.sleep(CHECK_INTERVAL_SECONDS)
            except Exception as loop_error:
                logger.error(f"❌ Userbot asosiy tsiklida xato: {loop_error}", exc_info=True)
                await asyncio.sleep(CHECK_INTERVAL_SECONDS)
    except FloodWaitError as e:
        logger.warning(f"FloodWaitError: {e.seconds} soniya kutilmoqda...")
        await asyncio.sleep(e.seconds)
    except RPCError as e:
        logger.error(f"Telegram RPC xatosi: {e}", exc_info=True)
    except Exception as e:
        logger.critical(f"Kutilmagan xato: {e}", exc_info=True)
    finally:
        if monitor.client and monitor.client.is_connected():
            await monitor.client.disconnect()
            logger.info("Userbot o'chirildi.")