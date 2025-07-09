import mysql.connector
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputMediaPhoto, ForceReply
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler, MessageHandler, filters


# Подключение к базе данных MySQL
def connect_to_db():
    connection = mysql.connector.connect(
        host='127.0.0.1',  # или IP сервера
        user='root',  # имя пользователя MySQL
        password='',  # пароль MySQL
        database='computer_shop'
    )
    return connection


# Получение информации о магазине
def get_store_info():
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM store_info WHERE id = 1")
    store_info = cursor.fetchone()
    conn.close()
    return store_info


# Получение списка продуктов
def get_products():
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    conn.close()
    return products


# Добавление товара в корзину пользователя
def add_to_cart(context, product_id, product_name):
    if 'cart' not in context.user_data:
        context.user_data['cart'] = []
    context.user_data['cart'].append({'product_id': product_id, 'product_name': product_name})


# Получение корзины пользователя
def get_user_cart(context):
    return context.user_data.get('cart', [])


# Функция запроса номера телефона
async def request_phone(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "Пожалуйста, введите ваш номер телефона:",
        reply_markup=ForceReply()
    )


# Обработка номера телефона
async def handle_phone_number(update: Update, context: CallbackContext) -> None:
    phone_number = update.message.text
    context.user_data['phone_number'] = phone_number
    await update.message.reply_text("Ваш номер телефона сохранён.")


# Оформление заказа
async def place_order(update: Update, context: CallbackContext) -> None:
    cart = get_user_cart(context)

    if 'phone_number' not in context.user_data:
        await update.callback_query.message.reply_text("Пожалуйста, введите ваш номер телефона с помощью команды /phone_number.")
        return

    customer_name = update.callback_query.from_user.full_name
    phone_number = context.user_data['phone_number']

    if not cart:
        await update.callback_query.message.reply_text("Ваша корзина пуста. Пожалуйста, добавьте товары в корзину.")
        return

    conn = connect_to_db()
    cursor = conn.cursor()

    for item in cart:
        cursor.execute(
            "INSERT INTO orders (product_id, product_name, customer_name, phone_number, status, order_date) VALUES (%s, %s, %s, %s, %s, NOW())",
            (item['product_id'], item['product_name'], customer_name, phone_number, "В обработке")
        )
    conn.commit()
    conn.close()

    keyboard = [
        [InlineKeyboardButton("Вернуться в главное меню", callback_data='start')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.message.reply_text(f"Ваши заказы оформлены. Мы свяжемся с вами для уточнения деталей.", reply_markup=reply_markup)

    context.user_data['cart'] = []


# Основные команды бота
async def start(update: Update, context: CallbackContext) -> None:
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        if query.message.text:
            await query.edit_message_text(
                "Привет! Я бот магазина компьютерных комплектующих. Чем могу помочь? Выберите команду:",
                reply_markup=main_menu_keyboard()
            )
        else:
            await query.message.reply_text(
                "Привет! Я бот магазина компьютерных комплектующих. Чем могу помочь? Выберите команду:",
                reply_markup=main_menu_keyboard()
            )
    else:
        await update.message.reply_text(
            "Привет! Я бот магазина компьютерных комплектующих. Чем могу помочь? Выберите команду:",
            reply_markup=main_menu_keyboard()
        )


def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("Информация о магазине", callback_data='storeinfo')],
        [InlineKeyboardButton("Товары", callback_data='products')],
        [InlineKeyboardButton("Мои заказы", callback_data='orders')],
        [InlineKeyboardButton("Корзина", callback_data='cart')],
    ]
    return InlineKeyboardMarkup(keyboard)


async def store_info(update: Update, context: CallbackContext) -> None:
    info = get_store_info()
    message = f"Магазин: {info[1]}\nАдрес: {info[2]}\nТелефон: {info[3]}\nСайт: {info[5]}\nПочта: {info[4]}"

    # Извлечение фото магазина
    photo = info[7]

    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("Вернуться в главное меню", callback_data='start')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_photo(photo=photo, caption=message, reply_markup=reply_markup)


async def products(update: Update, context: CallbackContext) -> None:
    products_list = get_products()

    query = update.callback_query
    await query.answer()

    for product in products_list:
        message = f"{product[1]} - {product[3]}₽\nОписание: {product[4]}"
        photo = product[6]

        keyboard = [
            [InlineKeyboardButton(f"Добавить в корзину: {product[1]} после покупкы", callback_data=f'add_{product[0]}')],
            [InlineKeyboardButton("Вернуться в главное меню", callback_data='start')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Отправляем сообщение с фото и кнопками
        await query.message.reply_photo(photo=photo, caption=message, reply_markup=reply_markup)


async def orders(update: Update, context: CallbackContext) -> None:
    conn = connect_to_db()
    cursor = conn.cursor()
    customer_name = update.callback_query.from_user.full_name
    cursor.execute("SELECT * FROM orders WHERE customer_name = %s", (customer_name,))
    orders_list = cursor.fetchall()
    conn.close()

    if orders_list:
        message = "Вот ваши заказы:\n"
        for order in orders_list:
            order_id = order[0]  # ID заказа
            product_id = order[1]  # ID товара
            product_name = order[2]  # Название товара
            customer_name = order[3]  # Имя заказчика
            phone_number = order [4] # Номер телефона
            status = order[5]  # Статус заказа
            order_date = order[6]  # Дата заказа

            # Формируем сообщение с правильными данными
            message += f"Заказ ID: {order_id}, Товар: {product_name}, ID товара: {product_id}, Заказчик: {customer_name}, Номер телефона: {phone_number},\n Статус: {status}, Дата: {order_date}\n"

        keyboard = [
            [InlineKeyboardButton("Вернуться в главное меню", callback_data='start')]
        ]
    else:
        message = "У вас нет заказов."
        keyboard = [
            [InlineKeyboardButton("Вернуться в главное меню", callback_data='start')]
        ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    query = update.callback_query
    await query.answer()
    await query.edit_message_text(message, reply_markup=reply_markup)


# Просмотр корзины
async def cart(update: Update, context: CallbackContext) -> None:
    cart = get_user_cart(context)

    if cart:
        message = "Ваши товары в корзине:\n"
        for item in cart:
            message += f"{item['product_name']}\n"
        message += "\nНажмите 'Оформить заказ' для завершения."
        keyboard = [
            [InlineKeyboardButton("Оформить заказ", callback_data='place_order')],
            [InlineKeyboardButton("Очистить корзину", callback_data='clear_cart')],
            [InlineKeyboardButton("Вернуться в главное меню", callback_data='start')]
        ]
    else:
        message = "Ваша корзина пуста. Пожалуйста, добавьте товары в корзину."
        keyboard = [
            [InlineKeyboardButton("Вернуться в главное меню", callback_data='start')]
        ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    query = update.callback_query
    await query.answer()
    await query.edit_message_text(message, reply_markup=reply_markup)


# Очистка корзины
async def clear_cart(update: Update, context: CallbackContext) -> None:
    context.user_data['cart'] = []  # Очищаем корзину

    keyboard = [
        [InlineKeyboardButton("Вернуться в главное меню", callback_data='start')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.answer()
    await update.callback_query.edit_message_text("Ваша корзина очищена.", reply_markup=reply_markup)


# Обработка нажатий на кнопки (выбор товара или команды)
async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'storeinfo':
        await store_info(update, context)
    elif query.data == 'products':
        await products(update, context)
    elif query.data == 'orders':
        await orders(update, context)
    elif query.data == 'cart':
        await cart(update, context)
    elif query.data == 'start':
        await start(update, context)
    elif query.data.startswith('add_'):
        product_id = int(query.data.split("_")[1])

        # Получаем информацию о товаре
        conn = connect_to_db()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM products WHERE id = %s", (product_id,))
        product_name = cursor.fetchone()[0]
        conn.close()

        # Добавляем товар в корзину
        add_to_cart(context, product_id, product_name)

        keyboard = [
            [InlineKeyboardButton("Вернуться в главное меню", callback_data='start')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Проверка на наличие текста в сообщении
        if query.message.text:
            await query.edit_message_text(f"Товар '{product_name}' добавлен в вашу корзину!", reply_markup=reply_markup)
        else:
            await query.message.reply_text(f"Товар '{product_name}' добавлен в вашу корзину!",
                                           reply_markup=reply_markup)

    elif query.data == 'place_order':
        await place_order(update, context)
    elif query.data == 'clear_cart':
        await clear_cart(update, context)


def main():
    TOKEN = '7272754177:AAFvAIKXOW_-Up_6L9YDFm_jQwasH-RQ7YA'
    application = Application.builder().token(TOKEN).build()

    # Команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("phone_number", request_phone))
    application.add_handler(MessageHandler(filters.TEXT, handle_phone_number))

    # Обработка нажатий на кнопки
    application.add_handler(CallbackQueryHandler(button))

    application.run_polling()


if __name__ == '__main__':
    main()
