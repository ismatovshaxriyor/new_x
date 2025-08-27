from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from template_bot.main import token
from database.models import User

def admin_required(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        user = User.select(User.telegram_id).where(User.bot_token == token).first()

        if user.telegram_id != user_id:
            await update.message.reply_text("❌ Siz bu botning egasi emassiz!")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper
