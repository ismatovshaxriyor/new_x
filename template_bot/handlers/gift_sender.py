import asyncio
import logging
import telegram

from database.models import User, Channels

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def process_single_request(app, gift_data):
    user_id = app.bot_data.get("user_id")
    premium_channels = get_premium_channels(gift_data)

    try:
        tasks = []

        # User uchun task
        if user_id:
            user = User.get_or_none(
                (User.telegram_id == user_id) & (User.send_to.in_(["user", "user_and_channel"]) & (User.is_monitoring_active == True))
            )
            if user is not None:
                tasks.append(lambda: process_user_gift_safe(app, user, gift_data))

        # Channels uchun tasklar
        for channel in premium_channels:
            tasks.append(lambda ch=channel: process_channel_gift_safe(app, ch, gift_data))

        if not tasks:
            logger.info("ℹ️ Hozirda faol premium foydalanuvchilar yoki kanallar topilmadi")
            return

        results = []
        for i, task_func in enumerate(tasks):
            if i > 0:
                await asyncio.sleep(2 * i)

            task = asyncio.create_task(task_func())
            result = await task
            results.append(result)

        return results

    except Exception as e:
        logger.error(f"❌ Gift yuborish jarayonida kutilmagan xato yuz berdi: {e}", exc_info=True)


# ========== USER PROCESSING ==========

async def process_user_gift_safe(context, user, gift_data):
    try:
        return await process_user_gift(context, user, gift_data)
    except Exception as e:
        logger.error(f"❌ Foydalanuvchi {user.telegram_id} ga gift yuborishda xatolik: {e}", exc_info=True)
        return "failed"

async def process_user_gift(context, user, gift_data):
    gift_id = gift_data['id']
    gift_stars = gift_data['stars']
    

    try:
        while True:
            gift_count = user.gift_count
            if user.min_stars > gift_stars or gift_stars > user.max_stars:
                return

            if user.gift_limit is not None and gift_count >= user.gift_limit:
                return

            await context.bot.send_gift(chat_id=user.telegram_id, gift_id=gift_id)
            user.gift_count += 1
            user.save()

            logger.info(f"✅ Gift #{gift_id} muvaffaqiyatli yuborildi - Foydalanuvchi: {user.telegram_id} ({user.gift_count}-chi gift)")
            await asyncio.sleep(1)

    except Exception as send_e:
        if 'Balance_too_low' in str(send_e):
            user.gift_count = 0
            user.is_monitoring_active = False
            user.save()
            await context.bot.send_message(
                chat_id=user.telegram_id, 
                text=f'⚠️ <b>Balans tugadi!</b>\n\n'
                     f'💰 Bot balansida {gift_stars} ⭐ starslik gift uchun yetarli mablag\' qolmagan.\n'
                     f'🔴 <b>Monitoring rejimi avtomatik o\'chirildi.</b>\n\n'
                     f'💡 Balansni to\'ldiring va qaytadan monitoring yoqing.',
                parse_mode='HTML'
            )
            return
        error_msg = str(send_e).lower()
        
        if 'stargift_usage_limited' in error_msg or 'limit' in error_msg:
            logger.warning(f"⚠️ Foydalanuvchi {user.telegram_id}: Kunlik gift limiti tugadi")
        else:
            logger.error(f"❌ Foydalanuvchi {user.telegram_id} ga gift yuborishda xato: {send_e}")
        
        return "failed"
    except telegram.error.RetryAfter as e:
        await asyncio.sleep(e.retry_after)
        await context.bot.send_message(
            chat_id=user.telegram_id, 
            text="🤖 <b>Bot qayta ishga tushmoqda...</b>\n\n"
                 "⏳ Iltimos, bir oz sabr qiling.",
            parse_mode='HTML'
        )

# ========== CHANNEL PROCESSING ==========

async def process_channel_gift_safe(context, channel, gift_data):
    try:
        return await process_channel_gift(context, channel, gift_data)
    except Exception as e:
        logger.error(f"❌ Kanal {channel.channel_name} ga gift yuborishda xatolik: {e}", exc_info=True)
        return "failed"

async def process_channel_gift(context, channel, gift_data):
    gift_id = gift_data['id']
    gift_stars = gift_data['stars']
    user = channel.user

    time_sleep = 1

    try:
        
        while True:
            gift_count = channel.gift_count
            if user.min_stars > gift_stars or gift_stars > user.max_stars:
                return

            if channel.gift_limit is not None and gift_count >= channel.gift_limit:
                return
                
            channel_id = channel.channel_id
            
            try:
                await context.bot.send_gift(chat_id=channel_id, gift_id=gift_id)
                channel.gift_count += 1
                channel.save()
                logger.info(f"✅ Gift #{gift_id} muvaffaqiyatli yuborildi - Kanal: {channel.channel_name} ({gift_count}-chi gift)")
                await asyncio.sleep(time_sleep)
            except Exception as e:
                raise e

    except Exception as send_e:
        if 'Balance_too_low' in str(send_e):
            channel.gift_count = 0
            user.is_monitoring_active = False
            user.save()
            channel.save()
            await context.bot.send_message(
                chat_id=user.telegram_id, 
                text=f'⚠️ <b>Balans tugadi!</b>\n\n'
                     f'💰 Bot balansida {gift_stars} ⭐ starslik gift uchun yetarli mablag\' qolmagan.\n'
                     f'📢 <b>Kanal:</b> {channel.channel_name}\n'
                     f'🔴 <b>Monitoring rejimi avtomatik o\'chirildi.</b>\n\n'
                     f'💡 Balansni to\'ldiring va qaytadan monitoring yoqing.',
                parse_mode='HTML'
            )
            return

        error_msg = str(send_e).lower()
        
        if 'stargift_usage_limited' in error_msg or 'limit' in error_msg:
            logger.warning(f"⚠️ Kanal {channel.channel_name}: Kunlik gift limiti tugadi")
        else:
            logger.error(f"❌ Kanal {channel.channel_name} ga gift yuborishda xato: {send_e}")
        
        return "failed"
    except telegram.error.RetryAfter as e:
        await asyncio.sleep(e.retry_after)
        await context.bot.send_message(
            chat_id=channel_id, 
            text="🎁 <b>Gift yuborish jarayoni davom etmoqda...</b>\n\n"
                 "⏳ Tez orada giftlar qayta yuboriladigan bo'ladi.",
            parse_mode='HTML'
        )

# ========== HELPER FUNCTIONS ==========

def get_premium_channels(gift):
    premium_users_with_channels = User.select().where(
        (User.is_premium == True) &
        (User.min_stars.is_null(False)) &
        (User.max_stars.is_null(False)) &
        (User.is_monitoring_active == True) &
        (User.min_stars <= gift['stars']) &
        (User.max_stars >= gift['stars']) &
        (User.send_to.in_(['channel', 'user_and_channel']))
    )
    
    channels = []
    for user in premium_users_with_channels:
        user_channels = Channels.select().where(
            (Channels.user == user) &
            ((Channels.gift_limit.is_null()) | (Channels.gift_limit > 0)) 
        )
        channels.extend(list(user_channels))
    
    return channels