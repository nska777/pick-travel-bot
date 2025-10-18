import asyncio
import os
import aiohttp
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.types import FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup, Update

# --- Токены ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- Groq клиент ---
session = None

async def create_groq_chat(messages):
    """
    Асинхронный запрос к Groq API.
    """
    global session
    if session is None:
        session = aiohttp.ClientSession()

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages
    }

    async with session.post(url, headers=headers, json=payload) as response:
        if response.status != 200:
            text = await response.text()
            raise Exception(f"Groq API error {response.status}: {text}")
        data = await response.json()
        return data["choices"][0]["message"]["content"]

# --- Память диалогов ---
user_chat_sessions = {}

# --- Главное меню ---
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🏝 Пляж 🌊", callback_data="tours_beach"),
            InlineKeyboardButton(text="🏰 Экскурсии 🗺️", callback_data="tours_excursion")
        ],
        [
            InlineKeyboardButton(text="🎿 Зимние ❄️", callback_data="tours_winter"),
            InlineKeyboardButton(text="🔥 Акции 🎁", callback_data="special")
        ],
        [
            InlineKeyboardButton(text="💬 Менеджер 🤖", callback_data="chat_ai"),
            InlineKeyboardButton(text="📞 Контакты 💬", callback_data="contacts")
        ]
    ])

def back_button():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_menu")]
    ])

# --- Команда /start ---
@dp.message(F.text == "/start")
async def start_command(message: types.Message):
    photo = FSInputFile("images/sea.jpg")
    await message.answer_photo(
        photo=photo,
        caption=(
            "<b>🌴 Добро пожаловать в Pick&Travels Tours!</b>\n\n"
            "🏖 У нас лучшие туры по всему миру — от Мальдив до Альп!\n"
            "Выберите направление или пообщайтесь с нашим виртуальным менеджером ✈️"
        ),
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu()
    )

# --- AI чат ---
@dp.callback_query(F.data == "chat_ai")
async def start_ai_chat(callback: types.CallbackQuery):
    user_chat_sessions[callback.from_user.id] = [
        {"role": "system", "content": (
            "Ты — дружелюбный менеджер турагентства Pick&Travels. "
            "Помогаешь клиентам подобрать туры, рассказываешь про направления, визы, отели и погоду. "
            "Отвечай тепло, с эмодзи, как хороший тур-менеджер."
        )}
    ]
    await callback.message.answer(
        "💬 Вы подключены к виртуальному менеджеру Pick&Travels!\n"
        "Можете спросить про туры, визы, страны или погоду ☀️\n\n"
        "Чтобы выйти, напишите <b>назад</b>.",
        parse_mode=ParseMode.HTML
    )

@dp.message()
async def chat_with_ai(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_chat_sessions:
        return

    if message.text.lower() in ["назад", "выйти", "меню"]:
        del user_chat_sessions[user_id]
        await message.answer("🏠 Возврат в главное меню 👇", reply_markup=main_menu())
        return

    user_chat_sessions[user_id].append({"role": "user", "content": message.text})

    try:
        reply_text = await create_groq_chat(user_chat_sessions[user_id])
        await message.answer(reply_text)
        user_chat_sessions[user_id].append({"role": "assistant", "content": reply_text})
    except Exception as e:
        await message.answer(f"⚠️ Ошибка при обращении к AI: {e}")

# --- Показ туров ---
async def show_tours(callback, tours):
    await callback.answer("⏳ Загружаем лучшие варианты...", show_alert=False)
    for t in tours:
        photo = FSInputFile(t["photo"])
        await callback.message.answer_photo(
            photo=photo,
            caption=f"<b>{t['name']}</b>\n\n{t['desc']}",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📲 Связаться", url="https://t.me/azizmarhabatours")],
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_menu")]
            ])
        )

# --- Категории ---
@dp.callback_query(F.data == "tours_beach")
async def tours_beach(callback: types.CallbackQuery):
    tours = [
        {"name": "🇲🇻 Мальдивы — Рай на Земле", "desc": "🏝 Всё включено 🍹, SPA 🤿\n💰 <b>$1,299</b> / 7 ночей", "photo": "images/maldives.jpg"},
        {"name": "🇹🇭 Таиланд — Энергия Азии", "desc": "🌅 Пхукет, Самуи 🏝️\n💰 <b>$899</b> / 10 дней", "photo": "images/thailand.jpg"},
        {"name": "🇪🇬 Египет — Солнце и история", "desc": "🐪 Хургада, сафари 🏺\n💰 <b>$499</b> / неделя", "photo": "images/egypt.jpg"}
    ]
    await show_tours(callback, tours)

@dp.callback_query(F.data == "tours_excursion")
async def tours_excursion(callback: types.CallbackQuery):
    tours = [
        {"name": "🇮🇹 Италия — Рим и Венеция", "desc": "🍕 История, романтика 🚤\n💰 <b>$1,199</b> / 9 дней", "photo": "images/italy.jpg"},
        {"name": "🇫🇷 Франция — Париж и Лазурный берег", "desc": "🗼 Эйфелева башня, Лувр 🎨\n💰 <b>$1,399</b> / 8 дней", "photo": "images/france.jpg"}
    ]
    await show_tours(callback, tours)

@dp.callback_query(F.data == "tours_winter")
async def tours_winter(callback: types.CallbackQuery):
    tours = [
        {"name": "🇨🇭 Швейцария — Альпы", "desc": "⛷ Церматт, Давос 🚐\n💰 <b>$1,499</b> / 8 дней", "photo": "images/switzerland.jpg"},
        {"name": "🇦🇹 Австрия — Горнолыжный рай", "desc": "🎿 Инсбрук, глинтвейн 🍷\n💰 <b>$1,099</b> / 7 дней", "photo": "images/austria.jpg"}
    ]
    await show_tours(callback, tours)

@dp.callback_query(F.data == "special")
async def special(callback: types.CallbackQuery):
    await callback.message.answer_photo(
        FSInputFile("images/special.jpg"),
        caption=("🎁 <b>ГОРЯЧЕЕ ПРЕДЛОЖЕНИЕ</b>\n\n"
                 "🇹🇷 Турция — 7 ночей / 5⭐ All Inclusive 🍹\n"
                 "✈️ Перелёт + трансфер\n\n"
                 "💰 <b>$399</b> / человек\n⏰ Только до конца недели!"),
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📲 Забронировать", url="https://t.me/azizmarhabatours")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_menu")]
        ])
    )

@dp.callback_query(F.data == "contacts")
async def contacts(callback: types.CallbackQuery):
    await callback.message.answer(
        "📍 <b>Офис:</b> Ташкент, ул. Аккурган, 22\n"
        "📞 +998 97 011 36 29\n"
        "📧 pickandtravell@gmail.com\n"
        "🌐 <a href='https://www.pick-and-travel.uz'>www.pick-and-travel.uz</a>\n"
        "👤 <a href='https://t.me/azizmarhabatours'>@azizmarhabatours</a>",
        parse_mode=ParseMode.HTML,
        reply_markup=back_button()
    )

@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery):
    await callback.message.answer("🏠 Главное меню 👇", reply_markup=main_menu())

# --- Webhook обработчик ---
async def webhook_handler(request):
    data = await request.json()
    update = Update.model_validate(data)
    await dp.feed_update(bot, update)
    return web.Response(text="ok")

# --- Render конфигурация ---
async def on_startup(app):
    webhook_url = f"https://pick-travel-bot.onrender.com/{TOKEN}"
    await bot.set_webhook(webhook_url)
    print(f"✅ Webhook установлен: {webhook_url}")

async def on_shutdown(app):
    await bot.delete_webhook()
    if session:
        await session.close()
    await bot.session.close()
    print("🛑 Webhook удалён")

# --- Запуск aiohttp ---
app = web.Application()
app.router.add_post(f"/{TOKEN}", webhook_handler)
app.router.add_get("/", lambda request: web.Response(text="Bot is alive!"))

app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
