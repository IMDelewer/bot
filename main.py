import asyncio
import os
import shutil
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

import json

with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

TOKEN = config["TOKEN"]
MAPS_FOLDER = config["MAPS_FOLDER"]
ACC_FOLDER = config["ACC_FOLDER"]
servers = config["servers"]

bot = Bot(token=TOKEN)
dp = Dispatcher()

class UpdateMap(StatesGroup):
    choose_folder = State()
    upload_file = State()
    
folder_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=server) for server in servers],
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

def search_in_acc_files(directory, search_text):
    if not os.path.exists(directory):
        print("Указанная папка не существует.")
        return
    
    for filename in os.listdir(directory):
        if filename.endswith(".acc"):
            file_path = os.path.join(directory, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    found = False
                    for line in file:
                        if search_text in line:
                            if not found:
                                print(f"Найдено в файле: {filename}")
                                found = True
                            print(f"  -> {line.strip()}")
            except Exception as e:
                print(f"Ошибка при чтении файла {filename}: {e}")
                
@dp.message(Command("update"))
async def update_command(message: types.Message, state: FSMContext):
    await message.answer("Выберите папку:", reply_markup=folder_keyboard)
    await state.set_state(UpdateMap.choose_folder)

@dp.message(Command("dp"))
async def dp_command(message: types.Message):
    target_files = []
    for root, dirs, files in os.walk(MAPS_FOLDER):
        for file in files:
            if file == "autoexec.cfg":
                full_path = os.path.join(root, file)
                target_files.append(full_path)
    if not target_files:
        await message.reply(":(")
        return
    for filepath in target_files:
        file = FSInputFile(filepath)
        await message.answer_document(file, caption=os.path.relpath(filepath, MAPS_FOLDER))
        
@dp.message(UpdateMap.choose_folder, F.text.in_(servers))
async def folder_chosen(message: types.Message, state: FSMContext):
    await state.update_data(folder=message.text)
    await message.answer("Теперь отправьте файл с расширением .map")
    await state.set_state(UpdateMap.upload_file)

@dp.message(UpdateMap.upload_file, F.document)
async def file_received(message: types.Message, state: FSMContext):
    data = await state.get_data()
    folder = data.get("folder")

    file_name = message.document.file_name
    if not file_name.endswith(".map"):
        await message.answer("Пожалуйста, отправьте файл с расширением .map")
        return

    file_path = f"{MAPS_FOLDER}/{folder}/data/maps/{file_name}"

    file = await bot.get_file(message.document.file_id)
    downloaded_file_path = f"/tmp/{file_name}"
    await bot.download_file(file.file_path, downloaded_file_path)

    if os.path.exists(file_path):
        os.remove(file_path)

    shutil.move(downloaded_file_path, file_path)

    await message.answer(f"Файл {file_name} обновлён в {folder}/data/maps/")
    await state.clear()

async def main():
    dp.include_router(dp)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
