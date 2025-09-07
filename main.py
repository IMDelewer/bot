import asyncio
import os
import shutil
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

TOKEN = ""
MAPS_FOLDER = "/root/F-DDrace/"
ACC_FOLDER = "/root/F-DDrace/build/data/accounts"
servers = ["build"]

bot = Bot(token=TOKEN)
dp = Dispatcher()

admins = [
    5665997196,
    6939807031
]
class UpdateMap(StatesGroup):
    choose_folder = State()
    upload_file = State()
    name = State()
    
folder_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=server) for server in servers],
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

keys = [
    "port", "logged_in", "disabled", "password", "username", "client_id",
    "level", "xp", "money", "kills", "deaths", "police_level", "survival_kills",
    "survival_wins", "spooky_ghost", "last_money_transaction_0",
    "last_money_transaction_1", "last_money_transaction_2", "last_money_transaction_3",
    "last_money_transaction_4", "vip", "block_points", "instagib_kills",
    "instagib_wins", "spawn_weapon_shotgun", "spawn_weapon_grenade",
    "spawn_weapon_rifle", "ninjajetpack", "last_player_name", "survival_deaths",
    "instagib_deaths", "taser_level", "killing_spree_record", "euros",
    "expire_date_vip", "portal_rifle", "expire_date_portal_rifle", "version",
    "addr", "last_addr", "taser_battery", "contact", "timeout_code",
    "security_pin", "register_date", "last_login_date", "flags", "email",
    "design", "portal_battery", "portal_blocker", "vote_menu_flags",
    "durak_wins", "durak_profit", "language"
]

def search_in_acc_files(directory, search_text):
    if not os.path.exists(directory):
        print("Указанная папка не существует.")
        return None
    
    for filename in os.listdir(directory):
        if filename.endswith(".acc"):
            file_path = os.path.join(directory, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    lines = [line.strip() for line in file if line.strip() != ""]
                    if any(search_text in line for line in lines):
                        print(f"Найдено в файле: {filename}")
                        # Формируем словарь
                        data = {key: (lines[i] if i < len(lines) else None) for i, key in enumerate(keys)}
                        return data  # возвращаем словарь для дальнейшего использования
            except Exception as e:
                print(f"Ошибка при чтении файла {filename}: {e}")
    
    print("Совпадений не найдено.")
    return None

import subprocess
import tempfile
     
@dp.message(Command("update"))
async def update_command(message: types.Message, state: FSMContext):
    if message.from_user.id in admins:
        await message.answer("Выберите папку:", reply_markup=folder_keyboard)
        await state.set_state(UpdateMap.choose_folder)
    else:
        pass

@dp.message(Command("dp"))
async def dp_command(message: types.Message):
    if message.from_user.id == 5665997196:
        full_path = os.path.join(MAPS_FOLDER, "build/Serverconfig.cfg")
        file = FSInputFile(full_path)
        await message.answer_document(file, caption=os.path.relpath(full_path, MAPS_FOLDER))
    else:
        pass
        
@dp.message(UpdateMap.choose_folder, F.text.in_(servers))
async def folder_chosen(message: types.Message, state: FSMContext):
    if message.from_user.id in admins:
        await state.update_data(folder=message.text)
        await message.answer("Теперь отправьте файл с расширением .map")
        await state.set_state(UpdateMap.upload_file)
    else:
        pass
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

@dp.message(Command("message"))
async def message_command(message: types.Message):
    try:
        result = subprocess.run(
            ["tmux", "capture-pane", "-p", "-S", "-", "-t", "block"],
            capture_output=True, text=True, check=True
        )
        logs = result.stdout.strip() or "Лог пуст."
    except subprocess.CalledProcessError:
        logs = ""

    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".log") as tmp:
        tmp.write(logs)
        tmp.flush()
        await message.answer_document(open(tmp.name, "rb"), filename="logs.log")

@dp.message(Command("mapss"))
async def mapss_command(message: types.Message):
    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        command_text = args[1]

    r = os.system(command_text)
    await message.answer(r)

@dp.message(Command("search"))
async def search_command(message: types.Message, state: FSMContext):
    if message.from_user.id in admins:
        await message.answer("Введите имя пользователя:")
        await state.set_state(UpdateMap.name)

@dp.message(UpdateMap.name)
async def process_name(message: types.Message, state: FSMContext):
    data = search_in_acc_files(ACC_FOLDER, message.text)
    await message.answer(f"""Юзернейм: {data["username"]}
Никнейм: {data["last_player_name"]}
Левел: {data["level"]}
Опыт: {data["xp"]}
Убийства: {data["kills"]}
Смерти: {data["deaths"]}
Полиция: {data["police_level"]}
Вип: {data["vip"]}
Спуки: {data.get("spook_ghost")}
Поинты: {data.get("block_points")}
""")
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
