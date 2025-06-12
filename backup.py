import os
import asyncio
import json
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler

API_TOKEN = 'YOUR_BOT_TOKEN'  # ← توکن ربات رو اینجا وارد کن
ADMIN_ID = 123456789          # ← آی‌دی عددی تلگرام شما

BACKUP_FILE = '/etc/x-ui/x-ui.db'
CONFIG_FILE = 'config.json'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()
channel_input_flag = {}

DEFAULT_CONFIG = {'interval': 12, 'channel_id': None, 'enabled': True}

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
            await bot.send_document(chat_id=ADMIN_ID, document=doc, caption='📦 بکاپ خودکار XUI')
            if config.get('channel_id'):
                await bot.send_document(chat_id=config['channel_id'], document=doc, caption='📦 بکاپ خودکار از پنل XUI')
    except Exception as e:
        await bot.send_message(chat_id=ADMIN_ID, text=f'❗ خطا در ارسال بکاپ: {e}')

def backup_job():
    asyncio.run(send_backup())

def get_main_keyboard():
    config = load_config()
    status = '🟢 فعال' if config.get('enabled', True) else '🔴 غیرفعال'
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton('📁 گرفتن بکاپ دستی', callback_data='backup')],
        [InlineKeyboardButton('⏱️ تنظیم زمان‌بندی بکاپ', callback_data='schedule')],
        [InlineKeyboardButton(f'⏯️ وضعیت زمان‌بندی: {status}', callback_data='toggle_scheduler')],
        [InlineKeyboardButton('📡 مدیریت کانال بکاپ', callback_data='manage_channel')]
    ])

def get_schedule_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton('⏰ هر 1 دقیقه (برای تست)', callback_data='set_1m')],
        [InlineKeyboardButton('⏰ هر 1 ساعت', callback_data='set_1')],
        [InlineKeyboardButton('⏰ هر 3 ساعت', callback_data='set_3')],
        [InlineKeyboardButton('⏰ هر 6 ساعت', callback_data='set_6')],
        [InlineKeyboardButton('⏰ هر 12 ساعت', callback_data='set_12')],
        [InlineKeyboardButton('⏰ هر 24 ساعت', callback_data='set_24')],
        [InlineKeyboardButton('🔙 بازگشت', callback_data='back_main')]
    ])

def get_channel_management_keyboard():
    config = load_config()
    current = config.get('channel_id') or 'تنظیم نشده'
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton('📥 ثبت/تغییر کانال', callback_data='set_channel')],
        [InlineKeyboardButton('❌ حذف کانال', callback_data='delete_channel')],
        [InlineKeyboardButton(f'ℹ️ کانال فعلی: {current}', callback_data='noop')],
        [InlineKeyboardButton('🔙 بازگشت', callback_data='back_main')]
    ])

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("⛔ دسترسی محدود است.")
    config = load_config()
    msg = f"👋 خوش اومدی به ربات بکاپ‌گیر XUI!\n\n📦 تنظیمات فعلی:\n⏱️ زمان‌بندی: هر {config.get('interval')} {'دقیقه' if config.get('interval') == 1 else 'ساعت'}\n📡 کانال: {config.get('channel_id') or 'تنظیم نشده'}\n⏯️ وضعیت: {'فعال' if config.get('enabled') else 'غیرفعال'}"
    await message.answer(msg, reply_markup=get_main_keyboard())

@dp.message_handler(content_types=types.ContentTypes.TEXT)
async def handle_text(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    if channel_input_flag.get(message.from_user.id):
        config = load_config()
        config['channel_id'] = message.text.strip()
        save_config(config)
        channel_input_flag[message.from_user.id] = False
        await message.reply(f"✅ آی‌دی کانال ذخیره شد: {message.text}", reply_markup=get_main_keyboard())
    else:
        await message.reply("❓ لطفاً از دکمه‌ها استفاده کن.")

@dp.callback_query_handler()
async def callback_handler(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return await callback.answer("⛔ دسترسی محدود.", show_alert=True)

    data = callback.data

    if data == 'backup':
        await send_backup()
        await callback.answer("📤 بکاپ دستی ارسال شد!")

    elif data == 'schedule':
        await callback.message.edit_text("⏱️ زمان‌بندی دلخواه را انتخاب کن:", reply_markup=get_schedule_keyboard())

    elif data.startswith('set_'):
        config = load_config()
        interval = 1 if data == 'set_1m' else int(data.split('_')[1])
        config['interval'] = interval
        save_config(config)
        scheduler.remove_all_jobs()
        scheduler.add_job(backup_job, 'interval', minutes=1 if interval == 1 else interval*60)
        await callback.message.edit_text(f"✅ زمان‌بندی بروزرسانی شد: هر {interval} {'دقیقه' if interval == 1 else 'ساعت'}", reply_markup=get_main_keyboard())

    elif data == 'toggle_scheduler':
        config = load_config()
        config['enabled'] = not config.get('enabled', True)
        save_config(config)
        await callback.message.edit_text("🔄 وضعیت زمان‌بندی تغییر کرد.", reply_markup=get_main_keyboard())
        await callback.answer("تغییر وضعیت انجام شد.")

    elif data == 'manage_channel':
        await callback.message.edit_text("📡 مدیریت کانال بکاپ:", reply_markup=get_channel_management_keyboard())

    elif data == 'set_channel':
        channel_input_flag[callback.from_user.id] = True
        await callback.message.edit_text("🔹 لطفاً آی‌دی یا لینک کانال خود را وارد کنید.\nمثال: @channel یا -100xxxxxxxxx")

    elif data == 'delete_channel':
        config = load_config()
        config['channel_id'] = None
        save_config(config)
        await callback.message.edit_text("✅ کانال حذف شد.", reply_markup=get_main_keyboard())

    elif data == 'back_main':
        await start_handler(callback.message)

async def on_startup(dp):
    config = load_config()
    if config.get('enabled', True):
        interval = config.get('interval', 12)
        if interval == 1:
            scheduler.add_job(backup_job, 'interval', minutes=1)
        else:
            scheduler.add_job(backup_job, 'interval', hours=interval)
    scheduler.start()
    await bot.send_message(ADMIN_ID, "✅ ربات با موفقیت راه‌اندازی شد و در حال اجراست.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
