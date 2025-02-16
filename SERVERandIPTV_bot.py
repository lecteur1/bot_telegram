import sqlite3
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

# إعدادات البوت
API_TOKEN = os.getenv("6640882317:AAGdPHhYLuSScQ92wld1icBxrU-PVrlXArk")  # توكن البوت
ADMIN_ID = int(os.getenv("1897119"))  # معرف المسؤول
BINANCE_ADDRESS = "YOUR_BINANCE_ADDRESS"  # عنوان الدفع عبر Binance

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)

# إنشاء قاعدة البيانات
conn = sqlite3.connect("shop.db", check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, price TEXT, description TEXT)''')
conn.commit()

# لوحة تحكم المسؤول
admin_kb = ReplyKeyboardMarkup(resize_keyboard=True)
admin_kb.add(KeyboardButton("إضافة منتج"), KeyboardButton("عرض المنتجات"), KeyboardButton("حذف منتج"))

# بدء البوت للمسؤول
@dp.message_handler(commands=['start'], user_id=ADMIN_ID)
async def start_admin(message: types.Message):
    await message.answer("مرحبًا بك في لوحة التحكم", reply_markup=admin_kb)

# إضافة منتج جديد
@dp.message_handler(lambda message: message.text == "إضافة منتج", user_id=ADMIN_ID)
async def add_product_prompt(message: types.Message):
    await message.answer("أرسل اسم المنتج والسعر والوصف مفصولين بفاصلة (اسم, سعر, وصف)")

@dp.message_handler(lambda message: "," in message.text and message.from_user.id == ADMIN_ID)
async def add_product(message: types.Message):
    name, price, description = message.text.split(",")
    c.execute("INSERT INTO products (name, price, description) VALUES (?, ?, ?)", (name.strip(), price.strip(), description.strip()))
    conn.commit()
    await message.answer("✅ تمت إضافة المنتج بنجاح")

# عرض المنتجات في لوحة التحكم
@dp.message_handler(lambda message: message.text == "عرض المنتجات", user_id=ADMIN_ID)
async def show_products_admin(message: types.Message):
    c.execute("SELECT * FROM products")
    products = c.fetchall()
    if not products:
        await message.answer("🚫 لا توجد منتجات بعد.")
        return
    for prod in products:
        await message.answer(f"{prod[0]} - {prod[1]}\nالسعر: {prod[2]}\n{prod[3]}")

# حذف منتج
@dp.message_handler(lambda message: message.text == "حذف منتج", user_id=ADMIN_ID)
async def delete_product_prompt(message: types.Message):
    await message.answer("🗑 أرسل ID المنتج الذي تريد حذفه")

@dp.message_handler(lambda message: message.text.isdigit() and message.from_user.id == ADMIN_ID)
async def delete_product(message: types.Message):
    product_id = int(message.text)
    c.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    await message.answer("✅ تم حذف المنتج بنجاح")

# عرض المنتجات للمستخدمين
@dp.message_handler(commands=['shop'])
async def show_products(message: types.Message):
    c.execute("SELECT * FROM products")
    products = c.fetchall()
    if not products:
        await message.answer("🚫 لا توجد منتجات متاحة حاليًا.")
        return
    for prod in products:
        buy_button = InlineKeyboardMarkup()
        buy_button.add(InlineKeyboardButton("🛒 شراء", callback_data=f"buy_{prod[0]}"))
        await message.answer(f"📌 {prod[1]}\n💰 السعر: {prod[2]}\n📖 {prod[3]}", reply_markup=buy_button)

# معالجة الشراء
@dp.callback_query_handler(lambda c: c.data.startswith("buy_"))
async def buy_product(callback_query: types.CallbackQuery):
    product_id = callback_query.data.split("_")[1]
    c.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = c.fetchone()
    if product:
        await bot.send_message(callback_query.from_user.id, f"لشراء {product[1]}, يرجى الدفع عبر Binance إلى العنوان التالي:\n\n🔗 {BINANCE_ADDRESS}")
        await bot.send_message(ADMIN_ID, f"🚨 طلب جديد:\n👤 المستخدم: {callback_query.from_user.full_name}\n🛒 المنتج: {product[1]}\n💰 السعر: {product[2]}")
    await callback_query.answer()

# تشغيل البوت
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
