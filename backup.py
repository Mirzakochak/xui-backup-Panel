# This code requires SSL support and external internet access to run properly.
# Since 'ssl' is unavailable in some sandbox environments, this code should be executed
# on a server with Python compiled with SSL support and access to pip-installed packages.

import os
import asyncio
import json
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler

API_TOKEN = 'YOUR_BOT_TOKEN'
ADMIN_ID = 123456789  # <-- عدد آی‌دی تلگرام خودت رو اینجا بذار
BACKUP_FILE = '/etc/x-ui/x-ui.db'
CONFIG_FILE = 'config.json'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()

DEFAULT_CONFIG = {'interval': 12, 'channel_id': None, 'enabled': True}
channel_input_flag = {}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def save_config(data):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f)

async def send_backup():
    config = load_config()
    if not os.path.exists(BACKUP_FILE):
        await bot.send_message(chat_id=ADMIN_ID, text='❗ فایل بکاپ یافت نشد.')
        return
    try:
        with open(BACKUP_FILE, 'rb') as doc:
            await bot.send_document(chat_id=ADMIN_ID, document=doc, caption='📦 بکاپ جدید ارسال شد.')
            if config.get('channel_id'):
                await bot.send_document(chat_id=config['channel_id'], document=doc, caption='📦 بکاپ خودکار از پنل XUI')
    except Exception as e:
        await bot.send_message(chat_id=ADMIN_ID, text=f'❗ خطا در ارسال بکاپ: {str(e)}')

def backup_job():
    config = load_config()
    if config.get('enabled', True):
        asyncio.run(send_backup())

def get_main_keyboard():
    config = load_config()
    status = '🟢 فعال' if config.get('enabled', True) else '🔴 غیرفعال'
    buttons = [
        [InlineKeyboardButton('📁 گرفتن بکاپ دستی', callback_data='backup')],
        [InlineKeyboardButton('⏱️ تنظیم زمان‌بندی بکاپ', callback_data='schedule')],
        [InlineKeyboardButton(f'⏯️ وضعیت زمان‌بندی: {status}', callback_data='toggle_scheduler')],
        [InlineKeyboardButton('📡 مدیریت کانال بکاپ', callback_data='manage_channel')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_schedule_keyboard():
    buttons = [
        [InlineKeyboardButton('⏰ هر 1 ساعت', callback_data='set_1')],
        [InlineKeyboardButton('⏰ هر 3 ساعت', callback_data='set_3')],
        [InlineKeyboardButton('⏰ هر 6 ساعت', callback_data='set_6')],
        [InlineKeyboardButton('⏰ هر 12 ساعت', callback_data='set_12')],
        [InlineKeyboardButton('⏰ هر 24 ساعت', callback_data='set_24')],
        [InlineKeyboardButton('🔙 بازگشت', callback_data='back_main')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_channel_management_keyboard():
    config = load_config()
    current = config.get('channel_id') or 'تنظیم نشده'
    buttons = [
        [InlineKeyboardButton('📥 ثبت/تغییر کانال', callback_data='set_channel')],
        [InlineKeyboardButton('❌ حذف کانال', callback_data='delete_channel')],
        [InlineKeyboardButton(f'ℹ️ کانال فعلی: {current}', callback_data='noop')],
        [InlineKeyboardButton('🔙 بازگشت', callback_data='back_main')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("⛔ دسترسی محدود است.")
    config = load_config()
    interval = config.get('interval', 12)
    channel = config.get('channel_id', 'تنظیم نشده')
    status = 'فعال' if config.get('enabled', True) else 'غیرفعال'
    msg = f"👋 خوش اومدی به ربات بکاپ‌گیر XUI!\n\n📦 تنظیمات فعلی:\n⏱️ زمان‌بندی: هر {interval} ساعت\n📡 کانال بکاپ: {channel}\n⏯️ وضعیت زمان‌بندی: {status}"
    await message.answer(msg, reply_markup=get_main_keyboard())

@dp.message_handler(content_types=types.ContentTypes.TEXT)
async def text_handler(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    if channel_input_flag.get(message.from_user.id):
        config = load_config()
        config['channel_id'] = message.text.strip()
        save_config(config)
        channel_input_flag[message.from_user.id] = False
        confirmation_text = (
            f"✅ آی‌دی کانال با موفقیت ذخیره شد: {message.text}\n"
            "📢 مطمئن شو که ربات به عنوان ادمین به کانال دسترسی داره."
        )
        await message.reply(confirmation_text, reply_markup=get_main_keyboard())
    else:
        await message.reply("❓ دستور نامشخص. لطفاً از دکمه‌ها استفاده کن.")

@dp.callback_query_handler()
async def callback_handler(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return await callback.answer("دسترسی محدود است.", show_alert=True)

    data = callback.data

    if data == 'backup':
        await send_backup()
        await callback.answer("📤 بکاپ ارسال شد!")

    elif data == 'schedule':
        await callback.message.edit_text("⏱️ یکی از زمان‌بندی‌های زیر را انتخاب کن:", reply_markup=get_schedule_keyboard())
        await callback.answer()

    elif data.startswith('set_') and data[4:].isdigit():
        hours = int(data.split('_')[1])
        config = load_config()
        config['interval'] = hours
        save_config(config)
        scheduler.remove_all_jobs()
        scheduler.add_job(backup_job, 'interval', hours=hours)
        await callback.message.edit_text(f"✅ زمان‌بندی تنظیم شد: هر {hours} ساعت", reply_markup=get_main_keyboard())
        await callback.answer("زمان‌بندی به‌روزرسانی شد")

    elif data == 'manage_channel':
        await callback.message.edit_text("📡 مدیریت کانال بکاپ:", reply_markup=get_channel_management_keyboard())
        await callback.answer()

    elif data == 'set_channel':
        channel_input_flag[callback.from_user.id] = True
        await callback.message.edit_text("📡 لطفاً آی‌دی یا لینک کانال خود را وارد کنید.\n📌 مثال: @your_channel یا -1001234567890")
        await callback.answer("در انتظار دریافت آی‌دی کانال")

    elif data == 'delete_channel':
        config = load_config()
        config['channel_id'] = None
        save_config(config)
        await callback.message.edit_text("❌ کانال بکاپ حذف شد.", reply_markup=get_main_keyboard())
        await callback.answer("کانال پاک شد")

    elif data == 'toggle_scheduler':
        config = load_config()
        config['enabled'] = not config.get('enabled', True)
        save_config(config)
        status = 'فعال' if config['enabled'] else 'غیرفعال'
        await callback.message.edit_text(f"⏯️ وضعیت زمان‌بندی تغییر کرد: {status}", reply_markup=get_main_keyboard())
        await callback.answer(f"وضعیت جدید: {status}")

    elif data == 'back_main':
        config = load_config()
        interval = config.get('interval', 12)
        channel = config.get('channel_id', 'تنظیم نشده')
        status = 'فعال' if config.get('enabled', True) else 'غیرفعال'
        msg = f"👋 خوش اومدی به ربات بکاپ‌گیر XUI!\n\n📦 تنظیمات فعلی:\n⏱️ زمان‌بندی: هر {interval} ساعت\n📡 کانال بکاپ: {channel}\n⏯️ وضعیت زمان‌بندی: {status}"
        await callback.message.edit_text(msg, reply_markup=get_main_keyboard())
        await callback.answer("بازگشت به منو")

async def on_startup(dp):
    config = load_config()
    scheduler.add_job(backup_job, 'interval', hours=config.get('interval', 12))
    scheduler.start()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
