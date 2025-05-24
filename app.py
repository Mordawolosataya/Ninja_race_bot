from flask import Flask
import threading
import bot  

app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is running!"

@app.route('/health')
def health():
    return "OK"

if __name__ == '__main__':
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=bot.main)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Запускаем Flask
    app.run(host='0.0.0.0', port=10000)
