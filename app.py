from flask import Flask
import threading
import os
import sys

# Импортируем ваш основной бот-файл
# Замените 'main' на название вашего файла без .py
try:
    import bot as bot_module
except ImportError:
    # Если файл называется по-другому, попробуйте
    import bot as bot_module

app = Flask(__name__)

@app.route('/')
def index():
    return "🤖 Ninja Race Bot is running!"

@app.route('/health')
def health():
    return {"status": "ok", "message": "Bot is healthy"}

@app.route('/status')
def status():
    return {"bot": "Ninja Race Bot", "status": "active"}

def start_bot():
    """Запускаем бота в отдельном потоке"""
    try:
        # Если в вашем боте есть функция main()
        if hasattr(bot_module, 'main'):
            bot_module.main()
        # Или если бот запускается при импорте
        else:
            print("Bot started successfully!")
    except Exception as e:
        print(f"Error starting bot: {e}")

if __name__ == '__main__':
    # Запускаем бота в фоновом потоке
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()
    
    # Запускаем Flask веб-сервер
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
