from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from database.models import User
from database.db import get_user
from config import MANAGER_ID, MANAGER_USERNAME
from .chech_agree_dec import require_agreement


async def start_command(update, context):
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name
    username = update.effective_user.username
    
    user, created = User.get_or_create(
        telegram_id=user_id,
        defaults={'username': username, "first_name": first_name}
    )

    text_for_default_user = f"""🎁 <b>Salom {first_name}!</b>
Kechirasiz botimiz faqat premium userlar uchun ishlaydi!

Agar siz ham premium user bo'lmoqchi bo'lsangiz /premium buyrug'ini bosing!"""
    
    text_for_premium_user = f"""🎁 <b>Salom {first_name}!</b>
Marhamat /help buyrug'i orqali imkoniyatlaringiz bilan tanishing
"""
    if user.is_premium:
        await update.message.reply_text(text_for_premium_user, parse_mode="HTML")
    else:
        await update.message.reply_text(text_for_default_user, parse_mode="HTML")

async def help_command(update, context):
    user_id = update.effective_user.id

    text_for_premium_user = """
🎯 <b>Premium Foydalanuvchi uchun qo'llanma</b>

✨ <b>Avtomatik Gift olish tizimi!</b>

🤖 Bot sizga avtomatik ravishda <b>sovg'alar (Gift)</b> ni olib beradi. 
Bu uchun quyidagi oddiy qadamlarni bajaring:

📋 <b>Qadma-qaddam yo'riqnoma:</b>

1️⃣ <b>@BotFather bilan ishlash</b>
   • @BotFather botga kiring
   • /start buyrug'ini bosing

2️⃣ <b>Yangi bot yaratish</b>
   • O'zingiz uchun yangi bot yarating
   • Bot API TOKEN ini nusxalang

3️⃣ <b>Token yuborish</b>
   • Nusxalangan API TOKEN ni bizning botimizga yuboring
   • /start_bot buyrug'idan foydalaning

4️⃣ <b>Sozlash</b>
   • Botingiz ishga tushgach unga kiring
   • Kerakli sozlamalarni amalga oshiring

5️⃣ <b>Natijani kuzatish</b>
   • Jarayonni kuzatishni boshlang
   • Hotirjamlik bilan kutib turing

🎁 <b>Tez orada sizning botingiz avtomatik Gift yig'a boshlaydi!</b>

💡 <i>Qo'shimcha yordam kerak bo'lsa, manager bilan bog'laning.</i>
"""

    user = await get_user(user_id)

    if user:
        if user.is_premium:
            await update.message.reply_text(text_for_premium_user, parse_mode="HTML")
    else:
        await update.message.reply_text('❌ <b>Siz ro\'yxatdan o\'tmagansiz!</b>\n\n🔥 Iltimos /start buyrug\'ini bosib ro\'yxatdan o\'ting', parse_mode="HTML")

@require_agreement
async def premium_command(update, context):
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name

    buttons_for_manager = [
        [InlineKeyboardButton(text='✅ Tasdiqlash', callback_data=f'approve_{user_id}')],
        [InlineKeyboardButton(text='❌ Rad etish', callback_data=f'reject_{user_id}')]
    ]

    user = await get_user(user_id)

    if user:
        if user.is_premium:
            await update.message.reply_text('🎉 <b>Tabriklaymiz!</b>\n\n⭐ Siz allaqachon <b>Premium</b> obunachisiz!', parse_mode="HTML")
            return
        else:
            await update.message.reply_text(f"""📤 <b>Premium so'rov yuborildi!</b>

⏳ Sizning premium so'rovingiz managerga yuborildi.

👨‍💼 Manager: {MANAGER_USERNAME}

💰 Manager bilan bog'lanib, to'lovni amalga oshirgach, manager sizning so'rovingizni tasdiqlaydi.

⚡ So'rov holati haqida xabardor bo'lib turasiz!""", parse_mode="HTML")
            
            await context.bot.send_message(
                chat_id=MANAGER_ID, 
                text=f"""🔔 <b>Yangi Premium So'rov!</b>

👤 <b>Foydalanuvchi:</b> {first_name}
🆔 <b>User ID:</b> <code>{user_id}</code>

⚡ Harakatni tanlang:""", 
                reply_markup=InlineKeyboardMarkup(buttons_for_manager),
                parse_mode="HTML"
            )
    else:
        await update.message.reply_text("❌ <b>Siz ro'yxatdan o'tmagansiz!</b>\n\n🚀 Iltimos /start buyrug'ini bosib ro'yxatdan o'ting!", parse_mode="HTML")


