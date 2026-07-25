import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ErrorEvent
from dotenv import load_dotenv
from aiohttp import web

logging.basicConfig(level=logging.INFO)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

ADMIN_GROUP_ID = -1004472350538
CHAT_INVITE_LINK = "https://t.me/+U3Hwif8vftkzMDc5"
CHANNEL_USERNAME = "@KAZE_house"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

RULES_TEXT = (
    "📜 **Правила для чата KAZE House:**\n\n"
    "**1. Уважение ко всем участникам**\n"
    "Запрещены: Оскорбления, травля, унижения, агрессия в адрес участников и администрации.\n"
    "→ *Наказание:* Варн. При повторе — Мут 1 час.\n\n"
    "**2. Спам и флуд**\n"
    "Запрещены: Повтор сообщений, больше 5 стикеров/гиф в ряд, бессмысленный набор символов (более 3 соо), реклама без согласия администрации.\n"
    "→ *Наказание:* Мут 30 мин (за спам), Мут 24 часа (за рекламу).\n\n"
    "**3. Запрещенный контент**\n"
    "Запрещено: 18+, насилие (картинки, стикеры), пропаганда наркотиков, призывы к незаконным действиям.\n"
    "→ *Наказание:* Бан навсегда (без права обжалования).\n\n"
    "**4. Право на конфиденциальность**\n"
    "Запрещено: Публиковать личные данные, переписки участников / администрации без их взаимного согласия.\n"
    "→ *Наказание:* Мут 24 часа (до выяснения ситуации).\n\n"
    "**5. Политика**\n"
    "Запрещено: Любые обсуждения политики, споры на политические темы, пропаганда и провокации.\n"
    "→ *Наказание:* Варн. При повторе — Мут 1 час.\n\n"
    "**6. Уважение администрации**\n"
    "Запрещено: Игнорирование слов администрации при конфликте или других перепалках.\n"
    "→ *Наказание:* Мут 1 час.\n\n"
    "───────────────\n"
    "Нажимай кнопку ниже, если согласен соблюдать правила!"
)

class Form(StatesGroup):
    rules = State()
    name = State()
    age = State()
    roblox_nick = State()
    skin_photo = State()

@dp.error()
async def error_handler(event: ErrorEvent):
    logging.error(f"Произошла ошибка: {event.exception}", exc_info=True)

async def check_subscription(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return False

async def show_rules_message(message_or_callback, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Ознакомился и согласен", callback_data="accept_rules")]
    ])
    if isinstance(message_or_callback, types.Message):
        await message_or_callback.answer(RULES_TEXT, reply_markup=kb, parse_mode="Markdown")
    else:
        await message_or_callback.message.answer(RULES_TEXT, reply_markup=kb, parse_mode="Markdown")
    await state.set_state(Form.rules)

@dp.message(CommandStart())
async def start_cmd(message: types.Message, state: FSMContext):
    await state.clear()
    if not await check_subscription(message.from_user.id):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Подписаться на канал", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
            [InlineKeyboardButton(text="Я подписался!", callback_data="check_sub")]
        ])
        await message.answer("⚠️ Для подачи анкеты нужно подписаться на наш Telegram-канал!", reply_markup=kb)
        return
    await show_rules_message(message, state)

@dp.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: types.CallbackQuery, state: FSMContext):
    if await check_subscription(callback.from_user.id):
        await callback.message.answer("Отлично, подписка подтверждена! 🎉")
        await show_rules_message(callback, state)
    else:
        await callback.answer("Вы всё ещё не подписаны на канал!", show_alert=True)

@dp.callback_query(F.data == "accept_rules", Form.rules)
async def rules_accepted(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Супер! Теперь заполни анкету. 🎭\n\nШаг 1 из 4: Как тебя зовут?")
    await state.set_state(Form.name)

@dp.message(Form.name, F.text)
async def process_name(message: types.Message, state: FSMContext):
    if len(message.text) > 30:
        await message.answer("Имя слишком длинное! Введи до 30 символов.")
        return
    await state.update_data(name=message.text)
    await message.answer("Шаг 2 из 4: Сколько тебе лет?")
    await state.set_state(Form.age)

@dp.message(Form.name)
async def process_name_invalid(message: types.Message):
    await message.answer("Пожалуйста, отправь имя текстом!")

@dp.message(Form.age, F.text)
async def process_age(message: types.Message, state: FSMContext):
    if not message.text.isdigit() or not (5 <= int(message.text) <= 99):
        await message.answer("Введи корректный возраст цифрами (например, 14)!")
        return
    await state.update_data(age=message.text)
    await message.answer("Шаг 3 из 4: Укажи твой ник в Roblox:")
    await state.set_state(Form.roblox_nick)

@dp.message(Form.age)
async def process_age_invalid(message: types.Message):
    await message.answer("Пожалуйста, введи возраст цифрами!")

@dp.message(Form.roblox_nick, F.text)
async def process_roblox(message: types.Message, state: FSMContext):
    await state.update_data(roblox_nick=message.text)
    await message.answer("Шаг 4 из 4: Отправь скриншот своего скина в Roblox 📸")
    await state.set_state(Form.skin_photo)

@dp.message(Form.roblox_nick)
async def process_roblox_invalid(message: types.Message):
    await message.answer("Пожалуйста, отправь ник текстом!")

@dp.message(Form.skin_photo, F.photo | F.document)
async def process_photo(message: types.Message, state: FSMContext):
    if message.photo:
        photo_file_id = message.photo[-1].file_id
    elif message.document and message.document.mime_type.startswith('image/'):
        photo_file_id = message.document.file_id
    else:
        await message.answer("Файл должен быть именно картинкой! Попробуй еще раз.")
        return

    user_data = await state.get_data()
    
    caption_text = (
        f"📝 **Новая анкета в KAZE House!**\n\n"
        f"👤 **Имя:** {user_data['name']}\n"
        f"🎂 **Возраст:** {user_data['age']}\n"
        f"🎮 **Roblox Nick:** {user_data['roblox_nick']}\n"
        f"🔗 **Профиль:** [{message.from_user.full_name}](tg://user?id={message.from_user.id})\n"
        f"🆔 **ID:** `{message.from_user.id}`"
    )

    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Принять 🎉", callback_data=f"accept_{message.from_user.id}"),
            InlineKeyboardButton(text="Отклонить 😔", callback_data=f"decline_{message.from_user.id}")
        ]
    ])

    try:
        await bot.send_photo(
            chat_id=ADMIN_GROUP_ID, 
            photo=photo_file_id, 
            caption=caption_text, 
            reply_markup=admin_kb, 
            parse_mode="Markdown"
        )
        await message.answer("Спасибо! Твоя анкета отправлена администраторам. Ожидай ответа! ✨")
        await state.clear()
    except Exception as e:
        logging.error(f"Ошибка при отправке анкеты: {e}")

@dp.message(Form.skin_photo)
async def process_photo_invalid(message: types.Message):
    await message.answer("Пожалуйста, пришли именно изображение (скриншот) своего скина!")

@dp.callback_query(F.data.startswith("accept_"))
async def accept_user(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    welcome_text = (
        "🎉 **ПОЗДРАВЛЯЕМ! ТВОЯ АНКЕТА ОДОБРЕНА!** 🎉\n\n"
        "Мы очень рады видеть тебя в числе участников **KAZE House**! 💫\n"
        f"👉 [Присоединиться к чату сообщества]({CHAT_INVITE_LINK})"
    )
    try:
        await bot.send_message(chat_id=user_id, text=welcome_text, parse_mode="Markdown")
        await callback.message.edit_caption(caption=f"{callback.message.caption}\n\n✅ **ПРИНЯТО** (Админ: {callback.from_user.first_name})", parse_mode="Markdown")
    except Exception:
        await callback.message.edit_caption(caption=f"{callback.message.caption}\n\n✅ **ПРИНЯТО** (У пользователя закрыто ЛС)", parse_mode="Markdown")

@dp.callback_query(F.data.startswith("decline_"))
async def decline_user(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    decline_text = "Сожалеем, но твоя анкета была отклонена администрацией. 😔"
    try:
        await bot.send_message(chat_id=user_id, text=decline_text)
        await callback.message.edit_caption(caption=f"{callback.message.caption}\n\n❌ **ОТКЛОНЕНО** (Админ: {callback.from_user.first_name})", parse_mode="Markdown")
    except Exception:
        await callback.message.edit_caption(caption=f"{callback.message.caption}\n\n❌ **ОТКЛОНЕНО** (У пользователя закрыто ЛС)", parse_mode="Markdown")

# -------------------------------------------------------------
# ВЕБ-СЕРВЕР ДЛЯ РЕНДЕРА (чтобы не падал из-за отсутствия портов)
# -------------------------------------------------------------
async def handle_ping(request):
    return web.Response(text="KAZE House Bot is online!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"Веб-сервер заглушка запущен на порту {port}")

# -------------------------------------------------------------
# ГЛАВНАЯ ТОЧКА ВХОДА
# -------------------------------------------------------------
async def main():
    # Запускаем фоновый веб-сервер для удовлетворения требований Render
    await start_web_server()
    
    # Запускаем прием сообщений Telegram
    logging.info("Запуск Telegram-бота...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
