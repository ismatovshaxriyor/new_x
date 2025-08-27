from telegram.ext import ConversationHandler, MessageHandler, CommandHandler, filters
from database.models import User
import requests
import subprocess
import logging
import asyncio
from handlers.check_premium_dec import premium_required

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GET_API_TOKEN, ACTIVE_BOT = range(2)

async def cancel_command(update, context):
    await update.message.reply_text('🚫 Jarayon bekor qilindi!')
    context.user_data.clear()
    return ConversationHandler.END

@premium_required
async def start_bot_command(update, context):
    await update.message.reply_text(
        '🤖 <b>Bot yaratish jarayonini boshlash</b>\n\n'
        '🔑 Iltimos, @BotFather dan olingan API tokenni yuboring:\n\n'
        '💡 <i>Masalan: 123456789:ABCdefGhijklMNOPqrstuvwxyz</i>',
        parse_mode='HTML'
    )
    return GET_API_TOKEN

async def active_bot(update, context):
    """Bot tokenni tekshirish va saqlash"""
    token = update.message.text.strip()
    
    if not token or ':' not in token:
        await update.message.reply_text(
            '❌ <b>Token formati noto\'g\'ri!</b>\n\n'
            '🔍 Iltimos, to\'g\'ri formatdagi tokenni kiriting.\n'
            '📝 Token formati: <code>123456:ABC-DEF1234ghIkl</code>',
            parse_mode='HTML'
        )
        return GET_API_TOKEN
    
    url = f"https://api.telegram.org/bot{token}/getMe"
    await update.message.reply_text(
        '⏳ <b>Botingiz ma\'lumotlari tekshirilmoqda...</b>\n\n'
        '🔄 Iltimos, bir oz kuting...',
        parse_mode='HTML'
    )
    asyncio.sleep(1)
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get('ok'):
            bot_info = data['result']
            bot_username = bot_info.get('username', 'Noma\'lum')
            bot_name = bot_info.get('first_name')
            
            context.user_data['token'] = token
            context.user_data['bot_username'] = bot_username
            context.user_data['bot_name'] = bot_name
            
            await update.message.reply_text(
                f"✅ <b>Bot muvaffaqiyatli tekshirildi!</b>\n\n"
                f"🤖 <b>Bot nomi:</b> {bot_name}\n"
                f"🔗 <b>Bot username:</b> @{bot_username}\n\n"
                f"🚀 <b>Botni ishga tushirish uchun</b> 'start' yuboring:",
                parse_mode='HTML'
            )
            return ACTIVE_BOT
        else:
            error_msg = data.get('description', 'Noma\'lum xato')
            await update.message.reply_text(
                f'❌ <b>Bot token yaroqsiz!</b>\n\n'
                f'📝 <b>Xato tafsiloti:</b> {error_msg}\n'
                f'🔄 Iltimos, boshqa token yuboring.',
                parse_mode='HTML'
            )
            return GET_API_TOKEN
            
    except requests.exceptions.Timeout:
        await update.message.reply_text(
            '⏱️ <b>So\'rov vaqti tugadi!</b>\n\n'
            '🔄 Iltimos, qaytadan urinib ko\'ring.\n'
            '🌐 Internet aloqangizni tekshiring.',
            parse_mode='HTML'
        )
        return GET_API_TOKEN
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}")
        await update.message.reply_text(
            '🔴 <b>Tarmoq xatosi!</b>\n\n'
            '📡 Internet aloqangizni tekshiring.\n'
            '🔄 Iltimos, qaytadan urinib ko\'ring.',
            parse_mode='HTML'
        )
        return GET_API_TOKEN
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        await update.message.reply_text(
            '❌ <b>Kutilmagan xato yuz berdi!</b>\n\n'
            '🔧 Iltimos, keyinroq qaytadan urinib ko\'ring.',
            parse_mode='HTML'
        )
        return GET_API_TOKEN


async def activate_bot(update, context):
    user_id = update.effective_user.id
    user_input = update.message.text.lower().strip()
    
    # Faqat 'start' buyrug'iga javob berish
    if user_input != 'start':
        await update.message.reply_text(
            "🚀 <b>Botni ishga tushirish uchun</b> 'start' yuboring\n\n"
            "🚫 Yoki /cancel bilan jarayonni to'xtating.",
            parse_mode='HTML'
        )
        return ACTIVE_BOT
    
    token = context.user_data.get('token')
    bot_username = context.user_data.get('bot_username')
    bot_name = context.user_data.get('bot_name')
    
    if not token:
        await update.message.reply_text(
            '❌ <b>Token topilmadi!</b>\n\n'
            '🔄 Iltimos, qaytadan boshlang.',
            parse_mode='HTML'
        )
        return ConversationHandler.END
    
    await update.message.reply_text(
        "🚀 <b>Botingiz ishga tushirilmoqda...</b>\n\n"
        "⏳ Bu jarayon bir necha soniya davom etishi mumkin...",
        parse_mode='HTML'
    )
    
    try:
        user = User.get(telegram_id=user_id)
        user.bot_token = token
        user.save()
        import os
        import sys

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
            debug_info = f"❌ <b>Bot fayli topilmadi!</b>\n\n"
            debug_info += f"📂 <b>Joriy papka:</b> {current_dir}\n"
            debug_info += f"📝 <b>Script joylashuvi:</b> {os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else 'N/A'}\n"
            debug_info += f"🔍 <b>Tekshirilgan yo'llar:</b>\n"
            for path in possible_paths:
                debug_info += f"  • {path}: {'✅' if os.path.exists(path) else '❌'}\n"
            
            # Directory tarkibini ko'rish
            if os.path.exists('template_bot'):
                files = os.listdir('template_bot')
                debug_info += f"\n📁 <b>template_bot papkasidagi fayllar:</b> {files}"
            else:
                debug_info += f"\n📁 <b>template_bot papkasi mavjud emas</b>"
                
            await update.message.reply_text(debug_info, parse_mode='HTML')
            return ConversationHandler.END
        

        python_cmd = sys.executable
        log_file = open(f"logs/{user_id}.log", "w")
        
        
        process = subprocess.Popen(
            [python_cmd, bot_file_path, '--token', token],
            stdout=log_file,
            stderr=log_file,
            cwd=current_dir,  
            env=os.environ.copy(),  
            shell=False  
        )
        
        return_code = process.poll()
        await asyncio.sleep(1)
        
        if return_code is None: 
            await update.message.reply_text(
                f"🎉 <b>Botingiz muvaffaqiyatli ishga tushdi!</b>\n\n"
                f"🤖 <b>Bot nomi:</b> {bot_name}\n"
                f"🔗 <b>Bot username:</b> @{bot_username}\n\n"
                f"✨ <b>Tabriklaymiz!</b> Endi botingizdan foydalanishingiz mumkin!\n"
                f"📱 Botga o'ting va /start buyrug'ini bosing.",
                parse_mode='HTML'
            )
            user.process_pid = process.pid
            user.save()
        elif return_code == 0:
            stdout, stderr = process.communicate()
            await update.message.reply_text(
                f"⚠️ <b>Bot ishga tushdi, lekin tez tugadi</b>\n\n"
                f"🔍 Log fayllarini tekshiring yoki qaytadan urinib ko'ring.",
                parse_mode='HTML'
            )
        else: 
            stdout, stderr = process.communicate()
            error_msg = f"❌ <b>Bot xato bilan tugadi</b> (kod: {return_code})\n\n"
            if stderr:
                error_msg += f"📝 <b>Xato:</b> <code>{stderr[:300]}</code>\n"
            if stdout:
                error_msg += f"📋 <b>Chiqish:</b> <code>{stdout[:300]}</code>"
            await update.message.reply_text(error_msg, parse_mode='HTML')
            
    except FileNotFoundError as e:
        await update.message.reply_text(
            f"❌ <b>Python yoki fayl topilmadi!</b>\n\n"
            f"📝 <b>Xato tafsiloti:</b> {str(e)}\n"
            f"🔧 Python o'rnatilganligini tekshiring.",
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Subprocess error: {e}")
        await update.message.reply_text(
            f"❌ <b>Xato yuz berdi!</b>\n\n"
            f"📝 <b>Tafsilot:</b> <code>{str(e)[:200]}</code>\n"
            f"🔄 Iltimos, qaytadan urinib ko'ring.",
            parse_mode='HTML'
        )
    
    context.user_data.clear()
    return ConversationHandler.END

active_bot_conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start_bot', start_bot_command)],
    states={
        GET_API_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, active_bot)],
        ACTIVE_BOT: [MessageHandler(filters.TEXT & ~filters.COMMAND, activate_bot)]
    },
    fallbacks=[CommandHandler('cancel', cancel_command)],
    per_user=True
)