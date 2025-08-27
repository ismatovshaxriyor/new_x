import asyncio
from datetime import datetime
from database.models import Gift, User, Channels
from concurrent.futures import ThreadPoolExecutor
from template_bot.handlers.gift_sender import process_single_request
from telegram.ext import Application

# ========== Giftlarni olish ==========
def get_new_gifts():
    query = Gift.select().where(
        (Gift.limited == True) & (Gift.sold_out == False)
    )
    return list(query)

def gift_to_dict(gift):
    return {
        'id': gift.id,
        'stars': gift.stars
    }

async def analyze_gift(gift: Gift, app: Application):
    gift_data = gift_to_dict(gift)
    user_id = app.bot_data.get("user_id")
    
    await process_single_request(app, gift_data)
    print(f"[{datetime.now()}] Gift ID={gift.id}, Stars={gift.stars} tahlil qilindi.")

# ========== Asosiy loop ==========
async def monitor_gifts(app: Application):
    loop = asyncio.get_event_loop()
    executor = ThreadPoolExecutor()

    while True:
        gifts = await loop.run_in_executor(executor, get_new_gifts)

        if gifts:
            print(f"{len(gifts)} ta yangi gift topildi")
            tasks = [asyncio.create_task(analyze_gift(g, app)) for g in gifts]
            await asyncio.gather(*tasks, return_exceptions=True)
        else:
            query = User.update({User.gift_count: 0}).where(User.gift_count != 0)
            query.execute()
            q_chnl = Channels.update({Channels.gift_count: 0}).where(Channels.gift_count != 0)
            q_chnl.execute()
            print("Yangi gift yo'q")

        await asyncio.sleep(3)  