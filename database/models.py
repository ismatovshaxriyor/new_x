from peewee import (
    Model, IntegerField, DateTimeField,
    BooleanField, AutoField, BigIntegerField, CharField, TextField, ForeignKeyField
)
from playhouse.pool import PooledSqliteDatabase
from datetime import datetime
import os

# Database path
DB_PATH = os.path.join("database", "main.db")

# Database sozlamalari bilan
database = PooledSqliteDatabase(
    DB_PATH,
    max_connections=100,  # Bir vaqtda 15 ta connection
    stale_timeout=300,   # 5 daqiqada ishlatilmagan connection'ni yopish
    timeout=30,          # 30 soniya timeout
    pragmas={
        'journal_mode': 'wal',        # Concurrent reads uchun
        'cache_size': -64 * 1000,     # 64MB cache
        'synchronous': 'normal',      # Performance/Safety balans
        'foreign_keys': 1,            # Foreign key constraint'lar
        'temp_store': 'memory',       # Temp ma'lumotlar RAM'da
    }
)

class BaseModel(Model):
    class Meta:
        database = database


class User(BaseModel):
    """Foydalanuvchi modeli"""
    user_id = AutoField(primary_key=True)  # Auto-increment ID
    telegram_id = BigIntegerField(unique=True, null=True, index=True)  # Telegram ID (katta bo'lishi mumkin)
    username = CharField(max_length=255, null=True, index=True)  # Username (255 karakter limit)
    first_name = CharField(max_length=255, null=True)  # Ism (255 karakter limit)
    bot_token = CharField(max_length=500, null=True)  # Bot token (uzun bo'lishi mumkin)
    process_pid = IntegerField(null=True)
    is_premium = BooleanField(default=False)  # Premium status
    is_agree = BooleanField(default=False)  # Kelishuv holati
    created_at = DateTimeField(default=datetime.now)  # Yaratilgan vaqt
    updated_at = DateTimeField(default=datetime.now)  # Yangilangan vaqt

    is_monitoring_active = BooleanField(default=False, null=True)
    min_stars = IntegerField(null=True)  
    max_stars = IntegerField(null=True)  
    gift_limit = IntegerField(null=True)
    gift_count = IntegerField(null=True, default=0)
    send_to = TextField(null=True, default='user') # "user" / "channel" / "user_and_channel"
    
    class Meta:
        table_name = 'users'
        indexes = (
            (('telegram_id', 'is_agree'), False),
            (('is_premium', 'created_at'), False),
        )

class Gift(BaseModel):
    id = BigIntegerField(primary_key=True)  # Manual ID (API dan keladi)
    stars = IntegerField(index=True)  # Yulduzlar soni
    limited = BooleanField(default=False, index=True)  # Limited edition
    sold_out = BooleanField(default=False, index=True)  # Sotilgan
    first_sale_date = DateTimeField(null=True)  # Birinchi sotuv sanasi
    last_sale_date = DateTimeField(null=True)  # Oxirgi sotuv sanasi
    created_at = DateTimeField(default=datetime.now)  # Qo'shilgan vaqt
    
    class Meta:
        table_name = 'gifts'
        indexes = (
            (('stars', 'sold_out'), False),
            (('limited', 'sold_out'), False),
        )

class Channels(BaseModel):
    user = ForeignKeyField(User, backref='user')
    channel_name = TextField()
    channel_id = IntegerField()
    gift_limit = IntegerField(null=True)
    gift_count = IntegerField(null=True, default=0)
