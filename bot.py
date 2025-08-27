from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, filters, PreCheckoutQueryHandler
from telegram import Update
import logging
import asyncio
import html
import os, sys

from config import API_TOKEN, ADMIN_ID
from database.db import init_db
from database.models import User
from handlers.user import (
    start_command,
    help_command, 
    premium_command
)
from handlers.manager import manager_callback, users_command, stop_bot_command, stop_premium_command
from handlers.admin import send_files
from handlers.chech_agree_dec import agreement_callback_handler
from handlers.activate_bot import active_bot_conv_handler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

global_app_instance: Application = None
def set_global_app_instance(app_instance: Application):
    global global_app_instance
    global_app_instance = app_instance


def get_global_app_instance() -> Application:
    """Global Application obyektini qaytaradi."""
    if global_app_instance is None:
        raise RuntimeError("Application obyekti hali o'rnatilmagan.")
    return global_app_instance

async def run_all_bots():
    query = User.select(User.telegram_id, User.bot_token).where(User.bot_token.is_null(False))
    
    for user in query:
        try:
            import os
            import sys
            import subprocess
            
            current_dir = os.getcwd()
            
            possible_paths = [
                'template_bot/main.py',
                os.path.join(current_dir, 'template_bot', 'main.py'),
                os.path.join(os.path.dirname(__file__), 'template_bot', 'main.py'),
                'template_bot\\main.py'  
            ]
            
            bot_file_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    bot_file_path = os.path.abspath(path)
                    break
            
            if not bot_file_path:
                debug_info = f"❌ Bot fayli topilmadi!\n\n"
                debug_info += f"Current dir: {current_dir}\n"
                debug_info += f"Script dir: {os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else 'N/A'}\n"
                debug_info += f"Tekshirilgan yo'llar:\n"
                for path in possible_paths:
                    debug_info += f"  - {path}: {'✓' if os.path.exists(path) else '✗'}\n"
                
                # Directory tarkibini ko'rish
                if os.path.exists('template_bot'):
                    files = os.listdir('template_bot')
                    debug_info += f"\ntemplate_bot papkasidagi fayllar: {files}"
                else:
                    debug_info += f"\ntemplate_bot papkasi mavjud emas"
                    
            
            python_cmd = sys.executable
            log_file = open(f"logs/{user.telegram_id}.log", "w")
            
            
            process = subprocess.Popen(
                [python_cmd, bot_file_path, '--token', user.bot_token],
                stdout=log_file,
                stderr=log_file,
                cwd=current_dir,  
                env=os.environ.copy(),  
                shell=False  
            )
            
            await asyncio.sleep(1)
            
            return_code = process.poll()
            
            if return_code is None: 
                user = User.get(telegram_id=user.telegram_id)
                user.bot_token = user.bot_token
                user.process_pid = process.pid
                user.save()
            elif return_code == 0:
                stdout, stderr = process.communicate()
            else: 
                stdout, stderr = process.communicate()
                error_msg = f"❌ Bot xato bilan tugadi (kod: {return_code})\n"
                if stderr:
                    error_msg += f"Xato: {stderr}"
                if stdout:
                    error_msg += f"\nChiqish: {stdout[:500]}"
                
        except Exception as e:
            logger.error(f"Subprocess error: {e}")

async def error_handler(update, context):
    import traceback
    traceback.print_exc()
    logger.error("Botda xatolik yuz berdi: %s", context.error)
    
    # Xato ma'lumotini saqlash
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    
    # Xato xabari uchun HTML matnini shakllantirish
    message = (
        "<b>Botda xatolik yuz berdi!</b>\n\n"
        f"<b>Update:</b> <pre>{html.escape(str(update_str))}</pre>\n\n"
        f"<b>Xatolik:</b> <pre>{html.escape(str(context.error))}</pre>\n\n"
        f"<b>Traceback:</b> <pre>{html.escape(tb_string)}</pre>"
    )
    
    # Adminka xabarni yuborish
    if ADMIN_ID:
        await context.bot.send_message(
            chat_id=ADMIN_ID, 
            text=message, 
            parse_mode='HTML'
        )

async def start_all():
    from services.telethon import main_userbot
    
    init_db()
    application = Application.builder().token(API_TOKEN).build()
    set_global_app_instance(application)
    
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('premium', premium_command))
    application.add_handler(CommandHandler('users', users_command))
    application.add_handler(CommandHandler('stop_bot', stop_bot_command))
    application.add_handler(CommandHandler('stop_premium', stop_premium_command))

    application.add_handler(CallbackQueryHandler(manager_callback, pattern=r"^(approve|reject)_\d+$"))
    application.add_handler(CallbackQueryHandler(agreement_callback_handler, pattern=r"^(agree|disagree)_\d+$"))
    application.add_handler(active_bot_conv_handler)


    application.add_error_handler(error_handler)
    application.add_handler(CommandHandler("get_logs", send_files))

    await run_all_bots()
    
    async with application:
        userbot_task = asyncio.create_task(main_userbot(application))
        
        await application.start()
        await application.updater.start_polling()
        
        await userbot_task
        
        await application.updater.stop()
        await application.stop()
    
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()


if __name__ == "__main__":
    asyncio.run(start_all())


