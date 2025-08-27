
async def pre_checkout_callback(update, context):
    query = update.pre_checkout_query

    if query.invoice_payload.startswith("stars_purchase_"):
        await query.answer(ok=True)
    else:
        await query.answer(ok=False, error_message="To'lov qilishda xatolik!")


