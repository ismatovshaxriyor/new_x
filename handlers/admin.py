from config import ADMIN_ID
import os

DB_FILE_NAME = 'database/main.db'

async def send_files(update, context) -> None:
    user_id = update.effective_user.id
    
    if user_id != int(ADMIN_ID):
        print(1)
        return
    
    if len(context.args) != 1 or not context.args[0].isdigit():
        await update.message.reply_text("Pidaraz to'g'ri ID yubor naxxuy")
        return

    target_user = int(context.args[0])

    LOG_FILE_NAME = f"logs/{target_user}.log"

    files_to_send = []

    # Log fayl mavjudligini tekshirish
    if os.path.exists(LOG_FILE_NAME):
        files_to_send.append((LOG_FILE_NAME, "📄 Bot log fayli"))
    else:
        await update.message.reply_text(
            "⚠️ <b>Log fayli topilmadi</b>",
            parse_mode="HTML"
        )

    # Database fayl mavjudligini tekshirish
    if os.path.exists(DB_FILE_NAME):
        files_to_send.append((DB_FILE_NAME, "🗄 Database fayli"))
    else:
        await update.message.reply_text(
            "⚠️ <b>Database fayli topilmadi</b>",
            parse_mode="HTML"
        )

    # Fayllarni yuborish
    if files_to_send:
        await update.message.reply_text(
            "📤 <b>Fayllar yuborilmoqda...</b>",
            parse_mode="HTML"
        )

        for file_path, caption in files_to_send:
            try:
                with open(file_path, "rb") as file:
                    await update.message.reply_document(
                        file,
                        caption=f"✅ {caption} muvaffaqiyatli yuborildi",
                        parse_mode="HTML"
                    )
            except Exception as e:
                await update.message.reply_text(
                    f"⚠️ <b>Xatolik:</b> {file_path} faylini yuborishda muammo yuz berdi.\n"
                    f"<code>{e}</code>",
                    parse_mode="HTML"
                )
    else:
        await update.message.reply_text(
            "ℹ️ Yuboriladigan fayllar topilmadi.",
            parse_mode="HTML"
        )
