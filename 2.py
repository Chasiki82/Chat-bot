import telebot
import re

bot = telebot.TeleBot('7272754177:AAFvAIKXOW_-Up_6L9YDFm_jQwasH-RQ7YA')

# Регулярные выражения для проверки корректности данных
email_pattern = re.compile(r"^[a-zA-Z0-9_.+-]+@(gmail\.com|mail\.ru|yandex\.ru)$")
phone_pattern = re.compile(r"^\+?\d{10,15}$")


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Я могу проверять корректность введенных данных: email, номер телефона, имя и фамилию.\nНачнем с вашего email:")


@bot.message_handler(func=lambda message: True)
def validate_data(message):
    user_input = message.text.split()

    if len(user_input) == 1:  # email
        email = user_input[0]
        if email_pattern.match(email):
            bot.reply_to(message, "Email корректен. Теперь введите номер телефона:")
            bot.register_next_step_handler(message, validate_phone, email)
        else:
            bot.reply_to(message, "Неверный формат email. Попробуйте еще раз:")


def validate_phone(message, email):
    phone = message.text
    if phone_pattern.match(phone):
        bot.reply_to(message, "Номер телефона корректен. Теперь введите ваше имя:")
        bot.register_next_step_handler(message, validate_first_name, email, phone)
    else:
        bot.reply_to(message, "Неверный формат номера телефона. Попробуйте еще раз:")
        bot.register_next_step_handler(message, validate_phone, email)


def validate_first_name(message, email, phone):
    first_name = message.text
    if first_name.isalpha():
        bot.reply_to(message, "Имя корректно. Теперь введите вашу фамилию:")
        bot.register_next_step_handler(message, validate_last_name, email, phone, first_name)
    else:
        bot.reply_to(message, "Имя может содержать только буквы. Попробуйте еще раз:")
        bot.register_next_step_handler(message, validate_first_name, email, phone)


def validate_last_name(message, email, phone, first_name):
    last_name = message.text
    if last_name.isalpha():
        bot.reply_to(message, "Ваши данные корректны!")
    else:
        bot.reply_to(message, "Фамилия может содержать только буквы. Попробуйте еще раз:")
        bot.register_next_step_handler(message, validate_last_name, email, phone, first_name)


bot.polling()
