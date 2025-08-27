from database.models import User
from telegram import BotCommand, BotCommandScopeChat
from config import MANAGER_ID, MANAGER_USERNAME, ADMIN_ID
import os
import signal

# Premium foydalanuvchi uchun buyruqlar ro'yxati
async def set_commands(application, chat_id):
    await application.bot.set_my_commands(
        [
            BotCommand("start", "🚀 Botni ishga tushirish"),
            BotCommand("help", "ℹ️ Yordam olish"),
            BotCommand("info", "Botingiz haqida ma'lumot")
        ],
        scope=BotCommandScopeChat(chat_id)
    )

# Manager callback tugmalari
async def manager_callback(update, context):
    query = update.callback_query
    data_sp = query.data.split('_')
    user_id = int(data_sp[1])
    user = User.get_or_none(telegram_id=user_id)

    await query.answer()

    if data_sp[0] == 'approve':
        if not user:
            await context.bot.send_message(
                MANAGER_ID, 
                "⚠️ <b>Xatolik:</b> Bunday foydalanuvchi topilmadi!",
                parse_mode="HTML"
            )
            return
        
        # Premium berish
        user.is_premium = True
        user.save()

        await query.message.delete()

        await context.bot.send_message(
            MANAGER_ID,
            f"✅ <b>{user.first_name}</b> premium foydalanuvchi qilindi!",
            parse_mode="HTML"
        )

        await context.bot.send_message(
            user_id,
            "🎉 <b>Tabriklaymiz!</b>\n"
            "Siz endi <b>Premium foydalanuvchi</b> bo'ldingiz! 🏆\n\n"
            "🔹 Yangi imkoniyatlar siz uchun ochildi.\n"
            "ℹ️ Qo'shimcha ma'lumot olish uchun /help buyrug'ini bosing.",
            parse_mode="HTML"
        )

        await set_commands(context.application, user_id)

    elif data_sp[0] == 'reject':
        await query.message.delete()

        await context.bot.send_message(
            MANAGER_ID,
            f"❌ <b>{user.first_name}</b> premium so'rovi rad etildi.",
            parse_mode="HTML"
        )

        await context.bot.send_message(
            user_id,
            f"⚠️ Premium so'rovingiz rad etildi.\n\n"
            f"Agar bu xato bo'lsa, iltimos <b>Manager</b> ({MANAGER_USERNAME}) bilan bog'laning.",
            parse_mode="HTML"
        )

async def stop_premium_command(update, context):
    user_id = update.effective_user.id

    if user_id == int(MANAGER_ID):
        if len(context.args) != 1 or not context.args[0].isdigit():
            await update.message.reply_text("Pidaraz to'g'ri ID yubor naxxuy")
        else:
            target_user = int(context.args[0])
            user = User.get(telegram_id=target_user)
            user.is_premium = False
            user.save()
            await update.message.reply_text(f"{user.first_name} ga dnx!")

async def stop_bot_command(update, context):
    user_id = update.effective_user.id
    if user_id == int(MANAGER_ID):
        if len(context.args) != 1 or not context.args[0].isdigit():
            await update.message.reply_text("Pidaraz to'g'ri pid yubor naxxuy")
        else:
            pid = int(context.args[0])
            result = stop_process(pid=pid)
            if result == True:
                user = User.get(User.process_pid == pid)
                user.bot_token = None
                user.process_pid = None
                user.save()
                await update.message.reply_text('Bot to\'xtadi naxxuy')
            elif result == 'not_found':
                await update.message.reply_text("Kunte blaaa, bunaqa pid bilan bot ishga tushmaganku!")

async def users_command(update, context):
    user_id = update.effective_user.id

    if user_id == int(ADMIN_ID):
        premiums_data = list(
            User.select(User.first_name, User.telegram_id, User.bot_token, User.process_pid).where(User.is_premium == True).dicts()
        )

        if not premiums_data:
            await update.message.reply_text("❌ Premium foydalanuvchilar topilmadi.")
            return

        text = ''
        for user_data in premiums_data:
            text += (
                f"👤 User: {user_data['first_name']}\n"
                f"🆔 User Id: <code>{user_data['telegram_id']}</code>\n"
                f"🔑 Bot token: {user_data['bot_token']}\n"
                f"⚙️ Process PID: <code>{user_data['process_pid']}</code>\n\n"
            )
        
        await update.message.reply_text(text, parse_mode="HTML")

def stop_process(pid, force = True):
    try:
        if force:
            os.kill(pid, signal.SIGKILL)  
            print(f"Process {pid} majburan to'xtatildi (SIGKILL).")
            return True
        else:
            os.kill(pid, signal.SIGTERM)  # yumshoq
            print(f"Process {pid} yumshoq to'xtatildi (SIGTERM).")
    except ProcessLookupError:
        print(f"Process {pid} topilmadi yoki allaqachon to'xtagan.")
        return 'not_found'
    except PermissionError:
        print(f"Process {pid} ni to'xtatishga ruxsat yo'q.")
    except Exception as e:
        print(f"Xato: {e}")