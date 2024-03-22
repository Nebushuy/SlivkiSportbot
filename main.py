#Slivki Sport chat bot
import asyncio
import datetime
import sqlite3
import random
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import plotly.graph_objects as go
from collections import defaultdict
#class YourState(StatesGroup):
#    waiting_for_params = State()

#storage = MemoryStorage()
# Инициализация бота и диспетчера
API_TOKEN = "6907418490:AAEEC1lr8FylzcsL73j3cxiQ_mX5JBEQy44"
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
#chat_id =-1002010915177

# Создание клавиатуры с кнопками команд
#commands_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
#commands_keyboard.add(KeyboardButton('/write'))
#commands_keyboard.add(KeyboardButton('/print'))
#commands_keyboard.add(KeyboardButton('/hist'))
#commands_keyboard.add(KeyboardButton('/clear'))

# Подключение к базе данных SQLite
conn = sqlite3.connect('workout_data.db')
cursor = conn.cursor()

# Создание таблицы для хранения данных о тренировках
cursor.execute('''CREATE TABLE IF NOT EXISTS workouts (day TEXT, name TEXT, type TEXT, qty INTEGER, chat_id INTEGER)''')
conn.commit()

phrases = {
    1: "Не останавливайся, даже если ты устал. Сегодняшние усилия приведут к завтрашнему успеху.",
    2: "Ты сильнее, чем думаешь. Верь в себя и двигайся вперед без страха.",
    3: "Каждый новый день - это новая возможность стать лучше, чем вчера. Используй её на все 100%.",
    4: "Трудности - это лишь шаги на пути к своей цели. Преодолевай их с улыбкой на лице.",
    5: "Твоя решимость и настойчивость - твои лучшие союзники на пути к успеху. Никогда не сомневайся в себе.",
    6: "Успех приходит к тем, кто не боится провалов и готов идти вперед, несмотря ни на что.",
    7: "Помни, что каждый пройденный этап приближает тебя к цели. Не останавливайся, иди дальше.",
    8: "Ты можешь достичь всего, о чем мечтаешь, если будешь работать упорно и не терять веры в себя.",
    9: "Самое важное - это начать действовать. Даже самый длинный путь начинается с первого шага.",
    10: "Будь настойчивым, стремись к лучшему и верь в свои силы. Ты способен на большее, чем думаешь."
}

# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer(
        "Привет!✌️ Я Сливки-бот, создан для записи твоих результатов!✊\nДля записи результатов напиши команду /write {Число отжиманий} {Число приседаний}\n Используй кнопки ниже для доступа к командам.\n/hist Выводит график результатов напокительным итогом\n /print Выводит результаты в виде набора данных", reply_markup=commands_keyboard)
    await schedule_random_phrases()

# Обработчик команды /write
@dp.message_handler(commands=['write'])
async def write_workout(message: types.Message):
    try:
        command, *args = message.text.split()
        day = args[2] if len(args) >= 3 else datetime.datetime.now().strftime("%Y-%m-%d")
        qty_pushups, qty_squats = map(int, args[:2])
        name = message.from_user.username
        chat_id = message.chat.id
        cursor.execute("INSERT INTO workouts VALUES (?, ?, ?, ?, ?)", (day, name, "pushups", qty_pushups, chat_id,))
        cursor.execute("INSERT INTO workouts VALUES (?, ?, ?, ?, ?)", (day, name, "squats", qty_squats, chat_id,))
        conn.commit()
        await message.answer(f"Данные успешно записаны: {qty_pushups} отжиманий\n{qty_squats} приседаний.\n{name}, ты просто красавчик!\nПродолжай в том же духе💪")
    except (ValueError, IndexError):
        await message.answer("Неверный формат команды. Используйте /write <qty_pushups> <qty_squats> <день в формате yyyy-mm-dd>")



# Обработчик команды /clear
@dp.message_handler(commands=['clear'])
async def clear_data(message: types.Message):
    chat_id = message.chat.id
    name = message.from_user.username
    cursor.execute("DELETE FROM workouts WHERE chat_id=? AND name=?", (chat_id, name))
    conn.commit()
    await message.answer("Данные успешно очищены.")

# Обработчик команды /print
@dp.message_handler(commands=['print'])
async def print_data(message: types.Message):
    chat_id = message.chat.id
    cursor.execute("SELECT day, name, type, qty FROM workouts WHERE chat_id=?", (chat_id,))
    data = cursor.fetchall()
    if not data:
        await message.answer("База данных пуста.")
    else:
        grouped_data = defaultdict(lambda: defaultdict(int))
        for row in data:
            name = row[1]
            exercise_type = row[2]
            qty = row[3]
            grouped_data[name][exercise_type] += qty

        result_text = ""
        for name, exercises in grouped_data.items():
            result_text += f"*{name}*\n"
            for exercise_type, total_qty in exercises.items():
                result_text += f"{exercise_type}: {total_qty}\n"
            result_text += "\n"
        await message.answer(result_text, parse_mode=ParseMode.MARKDOWN)

# Обработчик команды /hist
@dp.message_handler(commands=['hist'])
async def show_history(message: types.Message):
    chat_id = message.chat.id
    cursor.execute("SELECT day, name, type, qty FROM workouts WHERE chat_id=? ORDER BY day ASC", (chat_id,))
    data = cursor.fetchall()
    days = sorted(list(set([d[0] for d in data])))
    users = list(set([d[1] for d in data]))
    fig = go.Figure()
    for user in users:
        pushups_total = 0
        squats_total = 0
        x_values = [day for day in days]
        y_values_pushups = []
        y_values_squats = []
        for day in days:
            pushups_total += sum([d[3] for d in data if d[0] == day and d[1] == user and d[2] == "pushups"])
            squats_total += sum([d[3] for d in data if d[0] == day and d[1] == user and d[2] == "squats"])
            y_values_pushups.append(pushups_total)
            y_values_squats.append(squats_total)
        fig.add_trace(go.Scatter(x=x_values, y=y_values_pushups, mode='lines', name=f"{user} - pushups"))
        fig.add_trace(go.Scatter(x=x_values, y=y_values_squats, mode='lines', name=f"{user} - squats"))
    fig.update_layout(title='Workout History', xaxis_title='Day', yaxis_title='Cumulative Quantity')
    await bot.send_photo(message.chat.id, photo=fig.to_image(format="png"))

async def send_random_phrase():
    while True:
        current_hour = datetime.datetime.now().hour
        if current_hour == random.randint(9, 12) or current_hour == random.randint(13, 22):
            random_phrase = random.choice(phrases)
            await bot.send_message(chat_id, random_phrase)
        await asyncio.sleep(3600)  # Проверяем каждую минуту

# Добавляем задачу отправки случайной фразы в цикл событий
async def schedule_random_phrases():
    loop = asyncio.get_event_loop()
    loop.create_task(send_random_phrase())

# Запуск бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
