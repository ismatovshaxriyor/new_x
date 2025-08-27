from telegram import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice, BotCommand, BotCommandScopeChat

from database.models import User, Channels
from template_bot.handlers.decorators import admin_required

@admin_required
async def start_command(update, context):
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name
    username = update.effective_user.username
    
    text = f"""🎁 <b>Salom {first_name}!</b>

🌟 Men sizning shaxsiy botingizman.

📋 To'liq ma'lumot olish uchun /help buyrug'ini bosing."""
    
    await set_commands(context.application, user_id)
    await update.message.reply_text(text, parse_mode="HTML")

async def set_commands(application, chat_id):
    await application.bot.set_my_commands(
        [
            BotCommand("start", "🚀 Botni ishga tushirish"),
            BotCommand("help", "ℹ️ Yordam olish"),
            BotCommand("donate", "💰 Hisobni to'ldirish"),
            BotCommand("refund", "💳 Stars yechish"),
            BotCommand("start_process", "🎯 Gift kuzatuvini boshlash"),
            BotCommand("stop_process", "🛑 Gift kuzatuvini to'xtatish"),
            BotCommand("info", "⚙️ Sozlamalar haqida ma'lumot"),
            BotCommand("channels", "📢 Kanallarni boshqarish"),
        ],
        scope=BotCommandScopeChat(chat_id)
    )

@admin_required
async def help_command(update, context):
    text = """🎯 <b>Premium Foydalanuvchi uchun yo'riqnoma</b>

🤖 Men sizga avtomatik <b>Gift</b>larni olib beraman, buning uchun quyidagi qadamlarni bajaring:

<b>1️⃣ Gift oralig'ini va limitini belgilang:</b>
    <code>/set_gift_prefs &lt;minimal qiymat&gt; &lt;maksimal qiymat&gt; &lt;limit&gt;</code>

<b>2️⃣ Hisobingizni to'ldiring:</b>
    <code>/donate &lt;miqdori&gt;</code>

<b>3️⃣ Giftlarni kuzatishni ishga tushuring:</b>
    <code>/start_process</code>

━━━━━━━━━━━━━━━━━━━━━━━━━

📋 <b>Qo'shimcha buyruqlar:</b>
🛑 Kuzatishni to'xtatish - /stop_process
👤 Akkount haqida ma'lumot - /info
📺 Kanallar boshqaruvi - /channels
💰 To'lovni qaytarish - /refund"""

    await update.message.reply_text(text, parse_mode='HTML')

@admin_required
async def set_gift_prefs_command(update, context):
    user_id = update.effective_user.id
    
    if 2 > len(context.args) or len(context.args) > 3:
        await update.message.reply_text(
            "❌ <b>Noto'g'ri format!</b>\n\n"
            "📝 Iltimos, kamida ikkita raqam kiriting:\n"
            "💡 <b>Misol:</b> <code>/set_gift_prefs 100 500</code>\n\n"
            "🔢 <b>Format:</b> <code>/set_gift_prefs [min] [max] [limit]</code>",
            parse_mode="HTML"
        )
        return

    try:
        gift_limit = None
        if len(context.args) == 2:
            min_stars = int(context.args[0])
            max_stars = int(context.args[1])
        else:
            min_stars = int(context.args[0])
            max_stars = int(context.args[1])
            gift_limit = int(context.args[2])

        if max_stars < min_stars:
            await update.message.reply_text(
                "⚠️ <b>Xatolik!</b>\n\n"
                "📊 Iltimos, to'g'ri minimal va maksimal stars qiymatlarini kiriting.\n"
                "🔢 Minimal qiymat maksimaldan kichik bo'lishi kerak!",
                parse_mode="HTML"
            )
            return

        user = User.get_or_none(telegram_id=user_id)
        user.min_stars = min_stars
        user.max_stars = max_stars
        user.gift_limit = gift_limit
        user.save()

        if len(context.args) == 2:
            await update.message.reply_text(
                f"✅ <b>Sozlamalar saqlandi!</b>\n\n"
                f"⭐ <b>Minimal stars:</b> {min_stars}\n"
                f"🌟 <b>Maksimal stars:</b> {max_stars}\n\n"
                f"🎯 Endi siz {min_stars}-{max_stars} orasidagi giftlarni olasiz!",
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text(
                f"✅ <b>Sozlamalar saqlandi!</b>\n\n"
                f"⭐ <b>Minimal stars:</b> {min_stars}\n"
                f"🌟 <b>Maksimal stars:</b> {max_stars}\n"
                f"🎁 <b>Gift limiti:</b> {gift_limit}\n\n"
                f"🎯 Endi siz {min_stars}-{max_stars} orasidagi giftlarni olasiz!",
                parse_mode="HTML"
            )

    except (ValueError, IndexError):
        await update.message.reply_text(
            "❌ <b>Noto'g'ri format!</b>\n\n"
            "🔢 Iltimos, faqat raqam kiriting.\n"
            "💡 <b>Misol:</b> <code>/set_gift_prefs 100 500</code>",
            parse_mode="HTML"
        )

@admin_required
async def send_stars_invoice(update, context):
    chat_id = update.effective_chat.id
    
    if len(context.args) != 1:
        await update.message.reply_text(
            "❌ <b>Noto'g'ri format!</b>\n\n"
            "💰 Iltimos, yulduzlar miqdorini kiriting.\n"
            "💡 <b>Misol:</b> <code>/donate 500</code>",
            parse_mode="HTML"
        )
        return

    try:
        stars_amount = int(context.args[0])
        if stars_amount <= 0:
            await update.message.reply_text(
                "⚠️ <b>Xatolik!</b>\n\n"
                "🔢 Yulduzlar miqdori noldan katta bo'lishi kerak.\n"
                "💡 <b>Misol:</b> <code>/donate 100</code>",
                parse_mode="HTML"
            )
            return

    except ValueError:
        await update.message.reply_text(
            "❌ <b>Noto'g'ri format!</b>\n\n"
            "🔢 Iltimos, faqat raqam kiriting.\n"
            "💡 <b>Misol:</b> <code>/donate 500</code>",
            parse_mode="HTML"
        )
        return
    
    title = f"⭐ {stars_amount} Telegram Stars"
    description = f"💰 Hisobingizni {stars_amount} starsga to'ldirmoqchisiz!"
    payload = f"stars_purchase_{stars_amount}"
    provider_token = ""
    currency = "XTR" 
    
    price_unit = stars_amount
    prices = [LabeledPrice(label=f"⭐ {stars_amount} Yulduz", amount=price_unit)]

    await context.bot.send_invoice(
        chat_id=chat_id,
        title=title,
        description=description,
        payload=payload,
        provider_token=provider_token,
        currency=currency,
        prices=prices
    )

    await context.bot.send_message(
        text='💳 <b>To\'lov tafsilotlari yuborildi!</b>\n\n'
             '✅ To\'lovni amalga oshirgach hisobingizni tekshiring!\n'
             '📊 Balans yangilanishi haqida xabardor bo\'lasiz.',
        chat_id=chat_id,
        parse_mode="HTML"
    )

@admin_required
async def start_process_command(update, context):
    user_id = update.effective_user.id

    user = User.get(telegram_id=user_id)
    if (user.min_stars is None or user.max_stars is None) and user.is_premium:
        await update.message.reply_text(
            "⚙️ <b>Sozlamalar to'liq emas!</b>\n\n"
            "📊 Iltimos avval Gift sotib olish oralig'ini belgilang!\n\n"
            "💡 <b>Misol:</b> <code>/set_gift_prefs 100 500</code>",
            parse_mode="HTML"
        )
    elif user.is_premium:
        user.is_monitoring_active = True
        user.save()
        await update.message.reply_text(
            '🚀 <b>Giftlarni kuzatish boshlandi!</b>\n\n'
            '🎁 Yangi gift topilsa avtomatik yuboriladi\n'
            '⚡ Siz belgilagan sozlamalarga mos giftlar olinadi\n\n'
            '🛑 To\'xtatish uchun: /stop_process',
            parse_mode="HTML"
        )

@admin_required
async def stop_process_command(update, context):
    user_id = update.effective_user.id
    user = User.get(telegram_id=user_id)

    if user.is_premium:
        if user.is_monitoring_active == True:
            user.is_monitoring_active = False
            user.save()
            await update.message.reply_text(
                "⏹️ <b>Giftlarni kuzatish to'xtatildi!</b>\n\n"
                "❌ Yangi giftlar chiqsa avtomatik olib berilmaydi\n\n"
                "🚀 Qayta boshlash uchun: /start_process",
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text(
                "⏸️ <b>Jarayon allaqachon to'xtatilgan!</b>\n\n"
                "🚀 Boshlash uchun: /start_process",
                parse_mode="HTML"
            )

@admin_required
async def info_command(update, context):
    user_id = update.effective_user.id
    user = User.get_or_none(telegram_id=user_id)

    if user:
        if user.is_premium:
            status_emoji = "🟢" if user.is_monitoring_active else "🔴"
            status_text = "Faol" if user.is_monitoring_active else "Faol emas"
            
            text = f"""👤 <b>Profil Ma'lumotlari</b>

🆔 <b>Foydalanuvchi:</b> {user.first_name}
{status_emoji} <b>Kuzatish holati:</b> {status_text}

📊 <b>Gift sozlamalari:</b>
   🔻 <b>Minimal:</b> {user.min_stars if user.min_stars != None else '❌ Belgilanmagan'}
   🔺 <b>Maksimal:</b> {user.max_stars if user.max_stars != None else '❌ Belgilanmagan'}
   🎯 <b>Gift limiti:</b> {user.gift_limit if user.gift_limit else "♾️ Chegaralanmagan"}

📅 <b>Qo'shilgan sana:</b> {str(user.created_at).split(".")[0]}

📤 <b>Gift yuborish manzili:</b>"""
            
            check_user = "✅" if user.send_to == 'user' else "⚪"
            check_channel = "✅" if user.send_to == 'channel' else "⚪"
            check_channel_and_user = "✅" if user.send_to == 'user_and_channel' else "⚪"
            
            btns = [
                [InlineKeyboardButton(text=f"{check_user} O'zimga", callback_data='sendTo_user'), 
                InlineKeyboardButton(text=f"{check_channel} Kanallarga", callback_data='sendTo_channel')],
                [InlineKeyboardButton(text=f"{check_channel_and_user} O'zimga va Kanallarga", callback_data='sendTo_userAndChannel')]
            ]
            await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(btns), parse_mode="HTML")

@admin_required
async def refund_payment_command(update, context):
    try:
        if not context.args:
            await update.message.reply_text(
                "❌ <b>To'lov ID si kiritilmagan!</b>\n\n"
                "📝 To'lov ID sini kiriting:\n"
                "💡 <b>Misol:</b> <code>/refund 12345_67890_abcdef</code>",
                parse_mode="HTML"
            )
            return
            
        payment_id = context.args[0]
        user_id = update.effective_user.id

        user = User.get(telegram_id=user_id)

        await update.message.reply_text("⏳ <b>To'lov qaytarilmoqda...</b>\n\n⚡ Iltimos, kuting!", parse_mode="HTML")
        result = await context.bot.refund_star_payment(
            user_id=user_id,
            telegram_payment_charge_id=payment_id
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ <b>To'lovni qaytarishda xato!</b>\n\n"
            f"🚨 <b>Xato:</b> <code>{str(e)}</code>\n\n",
            parse_mode="HTML"
        )

@admin_required
async def channels_command(update, context):
    user_id = update.effective_user.id

    user = User.get(telegram_id=user_id)
    try:
        channels = list(Channels.select().where(Channels.user == user))
    except:
        channels = []

    btns = []
    if channels:
        for i, channel in enumerate(channels):
            btn = InlineKeyboardButton(
                text=f'📺 {i+1}. {channel.channel_name}', 
                callback_data=f'chnl_{channel.channel_id}'
            )
            
            if i % 2 == 0: 
                btns.append([btn])  
            else:  
                btns[-1].append(btn) 
        
        btns.append([InlineKeyboardButton(text='➕ Kanal qo\'shish', callback_data='add_channel')])
        await update.message.reply_text(
            '📺 <b>Sizning kanallaringiz:</b>\n\n'
            '🎁 Giftlar shu kanallarga yuboriladi\n'
            '⚙️ Boshqarish uchun kanal nomini bosing',
            reply_markup=InlineKeyboardMarkup(btns),
            parse_mode="HTML"
        )
    else:
        btns.append([InlineKeyboardButton(text='➕ Kanal qo\'shish', callback_data='add_channel')])
        await update.message.reply_text(
            '📺 <b>Kanallar bo\'limi</b>\n\n'
            '❌ Siz hali kanal qo\'shmadingiz\n\n'
            '💡 Kanal qo\'shib, giftlarni to\'g\'ridan-to\'g\'ri kanallaringizga yuboring!',
            reply_markup=InlineKeyboardMarkup(btns),
            parse_mode="HTML"
        )

async def pre_checkout_callback(update, context):
    query = update.pre_checkout_query

    if query.invoice_payload.startswith("stars_purchase_"):
        await query.answer(ok=True)
    else:
        await query.answer(ok=False, error_message="To'lov qilishda xatolik!")