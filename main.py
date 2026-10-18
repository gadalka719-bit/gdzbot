import asyncio
import io
import logging
import os

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from google import genai
from google.genai import types as genai_types
from PIL import Image

# 🔑 Считываем токены из переменных окружения Render
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

# Инициализируем официальный клиент Google GenAI
ai_client = genai.Client(api_key=GEMINI_API_KEY)

# Инструкция для ИИ-репетитора
SYSTEM_INSTRUCTION = (
    "Ты — умный помощник по учебе и ГДЗ. "
    "Распознай математическое или любое другое задание на изображении. "
    "Напиши понятный, пошаговый ход решения и выдели конечный ответ."
)

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(
        "👋 Привет! Я ГДЗ-помощник на базе **Google Gemini**.\n\n"
        "📸 **Отправь мне фото примера или задачи**, и я пришлю подробное решение!"
    )

@dp.message(F.photo)
async def handle_photo(message: types.Message):
    status_msg = await message.answer("🧠 Gemini разбирает задание с фото...")

    try:
        # 1. Получаем файл с наивысшим качеством из Telegram
        photo = message.photo[-1]
        file = await bot.get_file(photo.file_id)
        photo_bytes = await bot.download_file(file.file_path)

        # 2. Превращаем скачанные байты в изображение с помощью Pillow
        image = Image.open(io.BytesIO(photo_bytes.read()))

        # 3. Отправляем картинку и текстовый запрос в модель Gemini 2.5 Flash
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[image, "Реши задание с этого фото."],
            config=genai_types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.2,
            )
        )

        solution_text = response.text

        # 4. Отправляем готовое пошаговое решение пользователю
        await status_msg.edit_text(solution_text, parse_mode="Markdown")

    except Exception as e:
        logging.error(f"Ошибка при вызове Gemini API: {e}")
        await status_msg.edit_text("❌ Не удалось обработать фото. Попробуй отправить более четкий снимок.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())