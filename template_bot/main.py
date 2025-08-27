#!/usr/bin/env python3
import argparse
import logging
import sys
import os
import asyncio
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    PreCheckoutQueryHandler, ContextTypes
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from database.models import User
from template_bot.services.monitor_gifts import monitor_gifts
from template_bot.handlers.user import *
from template_bot.handlers.add_channels import add_channel_conv_handler
from template_bot.handlers.back_channel import back_channels_callback
from template_bot.handlers.delete_channels import delete_channel_callback
from template_bot.handlers.get_channel import get_channel_callback
from template_bot.handlers.sent_to_callback import set_sentTo_callback

from config import ADMIN_ID

# Argument parser
parser = argparse.ArgumentParser()
parser.add_argument('--token', required=True, help='Bot token')
args = parser.parse_args()
token = args.token

# Logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

global_app_instance: Application = None
def set_global_app_instance(app_instance: Application):
    global global_app_instance
    global_app_instance = app_instance


def get_global_app_instance() -> Application:
    if global_app_instance is None:
        raise RuntimeError("Application obyekti hali o'rnatilmagan.")
    return global_app_instance


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=ADMIN_ID, text=f'{context.error}')
    logger.error(f"Error: {context.error}")
    if update and update.message:
        try:
            await update.message.reply_text("❌ Xatolik yuz berdi!")
        except Exception as e:
            await context.bot.send_message(chat_id=ADMIN_ID, text=f'{e}')


if __name__ == "__main__":
    async def main():
        app = Application.builder().token(token).build()
        user = User.select(User.telegram_id).where(User.bot_token == token).first()
        app.bot_data["user_id"] = user.telegram_id

        # Handlerlar qo‘shamiz
        app.add_handler(CommandHandler('start', start_command))
        app.add_handler(CommandHandler('help', help_command))
        app.add_handler(CommandHandler('set_gift_prefs', set_gift_prefs_command))
        app.add_handler(CommandHandler('donate', send_stars_invoice))
        app.add_handler(CommandHandler("start_process", start_process_command))
        app.add_handler(CommandHandler("stop_process", stop_process_command))
        app.add_handler(CommandHandler('info', info_command))
        app.add_handler(CommandHandler("refund", refund_payment_command))
        app.add_handler(CommandHandler('channels', channels_command))

        app.add_handler(add_channel_conv_handler)
        app.add_handler(CallbackQueryHandler(get_channel_callback, pattern=r"^chnl_"))
        app.add_handler(CallbackQueryHandler(delete_channel_callback, pattern=r"^delete_"))
        app.add_handler(CallbackQueryHandler(back_channels_callback, pattern=r"back_channels"))
        app.add_handler(CallbackQueryHandler(set_sentTo_callback, pattern=r"^sendTo_"))
        app.add_handler(PreCheckoutQueryHandler(pre_checkout_callback))
        app.add_error_handler(error_handler)

        set_global_app_instance(app)

        # Botni qo'lda start qilish
        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)

        try:
            await asyncio.gather(
                monitor_gifts(app),
            )
        except Exception as e:
            print(e)

    asyncio.run(main())


