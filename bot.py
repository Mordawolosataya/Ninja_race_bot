import gspread
import os
from google.oauth2.service_account import Credentials
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from datetime import datetime

# Подключение к Google Sheets по ссылке
def connect_to_google_sheets():
    import json
    google_credentials_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
    creds = Credentials.from_service_account_info(json.loads(google_credentials_json), scopes=['https://www.googleapis.com/auth/spreadsheets'])

    client = gspread.authorize(creds)

    # Открытие Google Sheets по ссылке
    sheet = client.open_by_url(os.getenv('SHEETS_URL')).sheet1
    return sheet

# Проверка наличия обязательных заголовков в таблице
def check_headers(sheet):
    headers = sheet.row_values(1)
    required_headers = ['Дата', 'никнейм в Telegram', 'Имя', 'Накоплено', 'Цель']
    
    # Проверка наличия каждого обязательного заголовка
    for header in required_headers:
        if header not in headers:
            raise KeyError(f"Заголовок '{header}' не найден в таблице.")

# Проверка, есть ли пользователь в таблице
def user_exists_in_sheet(sheet, username):
    records = sheet.get_all_records()
    print(f"Поиск пользователя {username} в таблице...")  # Отладочное сообщение
    for record in records:
        if 'никнейм в Telegram' in record:
            print(f"Проверка строки: {record['никнейм в Telegram']}")  # Отладка для каждой строки
            if record['никнейм в Telegram'] == username:  # Ищем без символа @
                print("Пользователь найден!")  # Отладка, если пользователь найден
                return True
    print("Пользователь не найден.")  # Отладка, если пользователь не найден
    return False

# Получаем строку пользователя
def get_user_row(sheet, username):
    records = sheet.get_all_records()
    print(f"Поиск строки пользователя {username}...")  # Отладочное сообщение
    for index, record in enumerate(records):
        if 'никнейм в Telegram' in record:
            print(f"Проверка строки: {record['никнейм в Telegram']}")  # Отладка для каждой строки
            if record['никнейм в Telegram'] == username:  # Ищем без символа @
                print(f"Строка пользователя найдена: {index + 2}")  # Отладка, если строка найдена
                return index + 2  # +2, потому что первая строка заголовок
    print("Строка пользователя не найдена.")  # Отладка, если строка не найдена
    return None

# Проверка на достижение цели
async def check_goal_achieved(update: Update, context, username, current_amount, goal):
    print(f"Проверка цели для {username}: текущая сумма {current_amount}, цель {goal}")  # Отладка
    if current_amount >= goal:
        message = f"🎉 @{username}, вы достигли своей цели! Поздравляем! 🏆"
        image_url = "https://mec-krasnodar.ru/media/k2/items/cache/9dd60418066db724ebb1cf832eaf5702_L.jpg"  # Заменить на рабочую ссылку
        await update.message.reply_photo(photo=image_url, caption=message)
        print(f"Цель достигнута для {username}. Уведомление отправлено.")  # Отладка
    else:
        print(f"Цель еще не достигнута для {username}.")  # Отладка

# Обработка сообщений с хэштегом #ninja_race (обновление накопленной суммы)
async def handle_message(update: Update, context):
    message = update.message
    username = message.from_user.username
    
    if "#ninja_race" in message.text:
        try:
            amount = int(message.text.split()[-1])
            sheet = connect_to_google_sheets()

            if user_exists_in_sheet(sheet, username):
                user_row = get_user_row(sheet, username)
                if user_row:
                    current_amount = int(sheet.cell(user_row, 4).value)
                    goal = int(sheet.cell(user_row, 5).value)
                    new_amount = current_amount + amount
                    sheet.update_cell(user_row, 4, new_amount)  # Обновляем сумму
                    print(f"Обновление суммы для {username}: старая сумма {current_amount}, новая сумма {new_amount}, цель {goal}")  # Отладка

                    await check_goal_achieved(update, context, username, new_amount, goal)
                    await update.message.reply_text(f"💰 Ваш новый баланс: <b>{new_amount} рублей</b>", parse_mode='HTML')
            else:
                await update.message.reply_text(f"⚠️ @{username}, вы не зарегистрированы. Используйте команду /nr_go <Имя> <Цель> чтобы бот начал вести учет.")
        except ValueError:
            await update.message.reply_text("❗ Пожалуйста, укажите корректную сумму после хештега #ninja_race.")
            print("Ошибка: введена некорректная сумма.")  # Отладка

# Команда #nr_go (установить цель накопления)
async def nr_go(update: Update, context):
    try:
        name = context.args[0]
        goal = int(context.args[1])

        sheet = connect_to_google_sheets()
        user_data = [update.message.date.strftime("%Y-%m-%d"), update.message.from_user.username, name, 0, goal]
        sheet.append_row(user_data)

        await update.message.reply_text(f"🎯 Цель <b>{goal} рублей</b> установлена для {name}. Успешно добавлено в таблицу!", parse_mode='HTML')
    except IndexError:
        await update.message.reply_text("❗ Пожалуйста, укажите имя и цель в формате: /nr_go <Имя> <Цель>.")


# Обработка сообщений с хэштегом #ninja_race (обновление накопленной суммы)
async def handle_message(update: Update, context):
    message = update.message
    username = message.from_user.username
    
    if "#ninja_race" in message.text:
        try:
            # Извлекаем сумму
            amount = int(message.text.split()[-1])
            sheet = connect_to_google_sheets()

            # Проверяем, есть ли пользователь в таблице
            if user_exists_in_sheet(sheet, username):
                user_row = get_user_row(sheet, username)
                if user_row:
                    current_amount = int(sheet.cell(user_row, 4).value)
                    goal = int(sheet.cell(user_row, 5).value)
                    new_amount = current_amount + amount
                    sheet.update_cell(user_row, 4, new_amount)  # Обновляем сумму
                    print(f"Обновление суммы для {username}: старая сумма {current_amount}, новая сумма {new_amount}, цель {goal}")  # Отладка

                    # Проверяем, достиг ли пользователь цели
                    await check_goal_achieved(update, context, username, new_amount, goal)

                    await update.message.reply_text(f"Ваш новый баланс: {new_amount} рублей.")
            else:
                await update.message.reply_text(f"@{username}, вы не зарегистрированы. Используйте команду /nr_go <Имя> <Цель> чтобы бот начал вести учет.")
        except ValueError:
            await update.message.reply_text("Пожалуйста, укажите корректную сумму после хештега #ninja_race.")
            print("Ошибка: введена некорректная сумма.")  # Отладка

# Команда /nr_stats (выводит статистику пользователя)
async def nr_stats(update: Update, context):
    sheet = connect_to_google_sheets()
    username = update.message.from_user.username
    user_row = get_user_row(sheet, username)

    if user_row:
        date_start = sheet.cell(user_row, 1).value
        amount = int(sheet.cell(user_row, 4).value)
        goal = int(sheet.cell(user_row, 5).value)
        days_elapsed = (datetime.now() - datetime.strptime(date_start, "%Y-%m-%d")).days
        remaining = goal - amount

        await update.message.reply_text(
            f"📊 @{username}\n\n<b>Накоплено:</b> {amount} рублей\n<b>Прошло дней:</b> {days_elapsed}\n<b>Осталось:</b> {remaining} рублей", 
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text("⚠️ Вы не зарегистрированы. Используйте команду /nr_go <Имя> <Цель> чтобы бот начал вести учет.")

# Команда /nr_clear (очищает данные пользователя)
async def nr_clear(update: Update, context):
    try:
        sheet = connect_to_google_sheets()
        check_headers(sheet)
        username = update.message.from_user.username

        user_row = get_user_row(sheet, username)
        if user_row:
            sheet.delete_rows(user_row)
            await update.message.reply_text("🗑️ Ваши данные были удалены из таблицы.")
        else:
            await update.message.reply_text("⚠️ Ваши данные не найдены в таблице.")
    except KeyError as e:
        await update.message.reply_text(f"Ошибка: {str(e)}. Проверьте заголовки в таблице.")
    except Exception as e:
        await update.message.reply_text(f"Произошла ошибка: {str(e)}")

# Команда /nr_help (помощь)
async def nr_help(update: Update, context):
    help_text = """
    <b>💡 Список доступных команд:</b>
    /nr_go <Имя> <Цель> — Установить цель накопления.
    /nr_stats — Показать информацию о накоплениях.
    /nr_clear — Очистить данные и прекратить отслеживание.
    /nr_help — Показать это сообщение.
    """
    await update.message.reply_text(help_text, parse_mode='HTML')

# Основная функция для запуска бота
def main():
    print("Запуск бота...")
    app = ApplicationBuilder().token(os.getenv('BOT_TOKEN')).build()

    app.add_handler(CommandHandler('nr_go', nr_go))
    app.add_handler(CommandHandler('nr_stats', nr_stats))
    app.add_handler(CommandHandler('nr_clear', nr_clear))
    app.add_handler(CommandHandler('nr_help', nr_help))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(CallbackQueryHandler(button))

    app.run_polling()

# Пример встроенной клавиатуры для команды
async def show_menu(update: Update, context):
    keyboard = [
        [InlineKeyboardButton("📊 Статистика", callback_data='stats')],
        [InlineKeyboardButton("🗑️ Очистить данные", callback_data='clear')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)

    # Обработка нажатий на кнопки
async def button_handler(update: Update, context):
    query = update.callback_query
    if query.data == 'stats':
        await nr_stats(query, context)
    elif query.data == 'clear':
        await nr_clear(query, context)

# Обработка нажатия кнопок
async def button(update: Update, context):
    query = update.callback_query
    user = query.from_user
    if query.data == 'track':
        await query.message.reply_text(f"Пожалуйста, используйте команду /nr_go <Имя> <Цель> чтобы бот начал вести учет!")
    elif query.data == 'ignore':
        await query.message.reply_text("Хорошо. Если я вновь понадоблюсь, напишите /nr_help.")

if __name__ == '__main__':
    main()

    