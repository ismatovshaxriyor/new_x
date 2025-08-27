from peewee import SqliteDatabase
import os

DB_PATH = os.path.join("database", "main.db")
db = SqliteDatabase(DB_PATH)

def init_db():
    try:
        from .models import User, Gift, Channels
        db.connect()
        db.create_tables([User, Gift, Channels], safe=True)
        print("Ma'lumotlar bazasi ulandi va jadvallar yaratildi")
    except Exception as e:
        print(f"Ma'lumotlar bazasini ulashda xato: {str(e)}")
        raise


async def get_user(telegram_id: int):
    """Telegram ID bo'yicha foydalanuvchini qaytaradi."""
    from .models import User

    try:
        return User.get_or_none(User.telegram_id == telegram_id)
    except Exception as e:
        print(f"[DB] Foydalanuvchini olishda xato: {e}")
        return None
