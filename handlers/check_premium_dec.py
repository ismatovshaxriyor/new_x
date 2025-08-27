from functools import wraps
from telegram import Update
from telegram.ext import CallbackContext
from database.models import User

def premium_required(func):
    @wraps(func)
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        user_id = update.effective_user.id

        # Bazadan userni olish
        try:
            db_user = User.get(User.telegram_id == user_id)
        except User.DoesNotExist:
            if update.message:
                await update.message.reply_text("❌ Siz ro'yxatdan o'tmagansiz.")
            return

        # Premiumlikni tekshirish
        if db_user.is_premium:
            return await func(update, context, *args, **kwargs)
        else:
            if update.message:
                await update.message.reply_text("❌ Bu funksiyadan faqat Premium foydalanuvchilar foydalanishi mumkin.")
            elif update.callback_query:
                await update.callback_query.answer("❌ Premium talab qilinadi!", show_alert=True)
            return
    return wrapper