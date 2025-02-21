import telebot
from telebot import types
import sqlite3
import requests



bot = telebot.TeleBot('Ваш токен')

# Инициализация базы данных
conn = sqlite3.connect('baza_na_remont.db', check_same_thread=False)
cursor = conn.cursor()

# Создание таблицы, если она не существует
cursor.execute('''
    CREATE TABLE IF NOT EXISTS requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fio TEXT,
        phone TEXT,
        email TEXT,
        address TEXT,
        service TEXT
    )
''')
conn.commit()

# Состояния для обработки запросов
user_states = {}
USER_DATA = {}

# Функция для обработки команды /start
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_states[user_id] = 'waiting_for_fio'

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    item1 = types.KeyboardButton("Заполнить заявку")
    markup.add(item1)

    bot.send_message(message.chat.id, "Привет! Я бот для создания заявок на ремонт компьютеров.\nНажмите 'Заполнить заявку', чтобы начать.", reply_markup=markup)

# Обработчик для кнопки "Заполнить заявку"
@bot.message_handler(func=lambda message: message.text == "Заполнить заявку")
def get_fio(message):
    user_id = message.from_user.id
    user_states[user_id] = 'waiting_for_fio'
    bot.send_message(message.chat.id, "Пожалуйста, введите ваше ФИО:")

# Получение ФИО
@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == 'waiting_for_fio')
def get_phone(message):
    user_id = message.from_user.id
    USER_DATA[user_id] = {'fio': message.text}
    user_states[user_id] = 'waiting_for_phone'
    bot.send_message(message.chat.id, "Пожалуйста, введите ваш номер телефона для обратной связи:")

# Получение телефона
@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == 'waiting_for_phone')
def get_email(message):
    user_id = message.from_user.id
    USER_DATA[user_id]['phone'] = message.text
    user_states[user_id] = 'waiting_for_email'
    bot.send_message(message.chat.id, "Пожалуйста, введите ваш E-mail:")

# Получение email
@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == 'waiting_for_email')
def get_address(message):
    user_id = message.from_user.id
    USER_DATA[user_id]['email'] = message.text
    user_states[user_id] = 'waiting_for_address'
    bot.send_message(message.chat.id, "Пожалуйста, введите ваш адрес местонахождения для выезда:")

# Получение адреса
@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == 'waiting_for_address')
def get_service_type(message):
    user_id = message.from_user.id
    USER_DATA[user_id]['address'] = message.text
    user_states[user_id] = 'waiting_for_service'

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    item1 = types.KeyboardButton("Компьютер/ноутбук")
    item2 = types.KeyboardButton("Программное обеспечение")
    item3 = types.KeyboardButton("Периферийные устройства")
    markup.add(item1, item2, item3)

    bot.send_message(message.chat.id, "Выберите элемент сервиса:", reply_markup=markup)

# Получение элемента сервиса
@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == 'waiting_for_service')
def get_service_details(message):
    user_id = message.from_user.id
    USER_DATA[user_id]['service_type'] = message.text
    user_states[user_id] = 'waiting_for_service_details'

    if message.text == "Компьютер/ноутбук":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        item1 = types.KeyboardButton("Не включается")
        item2 = types.KeyboardButton("Медленно работает")
        item3 = types.KeyboardButton("Зависает")
        markup.add(item1, item2, item3)
        bot.send_message(message.chat.id, "Выберите проблему:", reply_markup=markup)

    elif message.text == "Программное обеспечение":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        item1 = types.KeyboardButton("Помощь с установкой программ")
        item2 = types.KeyboardButton("Проверить/почистить от вирусов")
        item3 = types.KeyboardButton("Не запускается/вылетает программа")
        item4 = types.KeyboardButton("Установка/переустановка ОС")
        markup.add(item1, item2, item3, item4)
        bot.send_message(message.chat.id, "Выберите проблему:", reply_markup=markup)

    elif message.text == "Периферийные устройства":
        bot.send_message(message.chat.id, "Опишите проблему с периферийным устройством:")
        user_states[user_id] = 'waiting_for_peripheral_description'

    else:
        bot.send_message(message.chat.id, "Некорректный выбор элемента сервиса.")
        user_states[user_id] = None

# Получение деталей сервиса (для "Компьютер/ноутбук" и "Программное обеспечение")
@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == 'waiting_for_service_details')
def save_request(message):
    user_id = message.from_user.id
    USER_DATA[user_id]['service_details'] = message.text

    # Сохранение в базу данных
    fio = USER_DATA[user_id]['fio']
    phone = USER_DATA[user_id]['phone']
    email = USER_DATA[user_id]['email']
    address = USER_DATA[user_id]['address']
    service = f"{USER_DATA[user_id]['service_type']}: {USER_DATA[user_id]['service_details']}"

    cursor.execute('''
        INSERT INTO requests (fio, phone, email, address, service)
        VALUES (?, ?, ?, ?, ?)
    ''', (fio, phone, email, address, service))
    conn.commit()

    bot.send_message(message.chat.id, "Заявка успешно создана и сохранена!")
    del user_states[user_id]  # Сброс состояния
    del USER_DATA[user_id]

    markup = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, "Что-нибудь еще?", reply_markup=markup)

# Получение описания проблемы с периферийным устройством
@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == 'waiting_for_peripheral_description')
def save_request_peripheral(message):
    user_id = message.from_user.id
    USER_DATA[user_id]['service_details'] = message.text

    # Сохранение в базу данных
    fio = USER_DATA[user_id]['fio']
    phone = USER_DATA[user_id]['phone']
    email = USER_DATA[user_id]['email']
    address = USER_DATA[user_id]['address']
    service = f"Периферийные устройства: {USER_DATA[user_id]['service_details']}"

    cursor.execute('''
        INSERT INTO requests (fio, phone, email, address, service)
        VALUES (?, ?, ?, ?, ?)
    ''', (fio, phone, email, address, service))
    conn.commit()

    bot.send_message(message.chat.id, "Заявка успешно создана и сохранена! Скоро с Вами свяжутся")
    del user_states[user_id]  # Сброс состояния
    del USER_DATA[user_id]

    markup = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, "Что-нибудь еще?", reply_markup=markup)

# Обработчик для любого другого текста
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "Я не понимаю эту команду. Пожалуйста, используйте /start или кнопку 'Заполнить заявку'.")

# Запуск бота
if __name__ == '__main__':
    try:
        bot.polling(none_stop=True)
    finally:
        conn.close() # Закрываем соединение с базой данных после остановки бота