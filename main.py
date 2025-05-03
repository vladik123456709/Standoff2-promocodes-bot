import time
import requests
import json
import threading
from bs4 import BeautifulSoup
from telegram import (
    Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    Updater, CommandHandler, CallbackQueryHandler
)

TOKEN = "7974244810:AAGi-uKUQl3uczoWDL8yWzprji2LDtqGMqM"
CHAT_ID = 7632292818
CHECK_INTERVAL = 30  # секунд

last_codes = set()
auto_search = False

# Загрузка фильтров
try:
    with open("filters.json", "r") as f:
        filters = json.load(f)
except FileNotFoundError:
    filters = {"нож": True, "голда": True, "перчатки": True}

def save_filters():
    with open("filters.json", "w") as f:
        json.dump(filters, f)

def get_sources():
    return [
        "https://example1.com",
        "https://example2.com",
        "https://example3.com"
    ]

def fetch_codes():
    codes = []
    for url in get_sources():
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
            for tag in soup.find_all("code"):
                code = tag.text.strip()
                if any(word in code.lower() for word in filters if filters[word]):
                    codes.append(code)
        except:
            continue
    return codes

def search_and_send(bot: Bot):
    global last_codes
    new_codes = fetch_codes()
    found_new = False
    for code in new_codes:
        if code not in last_codes:
            bot.send_message(chat_id=CHAT_ID, text=f"Новый промокод: `{code}`", parse_mode="Markdown")
            last_codes.add(code)
            found_new = True
    if not found_new:
        bot.send_message(chat_id=CHAT_ID, text="Пока нет новых промокодов.")

def start_auto_search(bot: Bot):
    def run():
        global auto_search
        while auto_search:
            search_and_send(bot)
            time.sleep(CHECK_INTERVAL)
    threading.Thread(target=run, daemon=True).start()

def start(update: Update, context):
    keyboard = [
        [InlineKeyboardButton("🔍 Найти промокоды", callback_data="find")],
        [InlineKeyboardButton("⛔ Остановить поиск", callback_data="stop")],
        [InlineKeyboardButton("⚙️ Настроить фильтр", callback_data="filter")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Выберите действие:", reply_markup=reply_markup)

def button(update: Update, context):
    global auto_search
    query = update.callback_query
    query.answer()
    bot = context.bot

    if query.data == "find":
        search_and_send(bot)
    elif query.data == "stop":
        auto_search = False
        query.edit_message_text("Автопоиск остановлен.")
    elif query.data == "filter":
        toggle_filter_buttons(query)

def toggle_filter_buttons(query):
    keyboard = [
        [InlineKeyboardButton(f"Нож: {'✅' if filters['нож'] else '❌'}", callback_data="filter_нож")],
        [InlineKeyboardButton(f"Голда: {'✅' if filters['голда'] else '❌'}", callback_data="filter_голда")],
        [InlineKeyboardButton(f"Перчатки: {'✅' if filters['перчатки'] else '❌'}", callback_data="filter_перчатки")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back")]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text("Настройки фильтра:", reply_markup=markup)

def filter_toggle(update: Update, context):
    query = update.callback_query
    query.answer()
    key = query.data.split("_")[1]
    filters[key] = not filters[key]
    save_filters()
    toggle_filter_buttons(query)

def handle_back(update: Update, context):
    query = update.callback_query
    query.answer()
    start(update, context)

def handle_autostart(update: Update, context):
    global auto_search
    auto_search = True
    update.message.reply_text("Автопоиск включён. Проверка каждые 30 секунд.")
    start_auto_search(context.bot)

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("автостарт", handle_autostart))
    dp.add_handler(CallbackQueryHandler(button, pattern="^(find|stop|filter)$"))
    dp.add_handler(CallbackQueryHandler(filter_toggle, pattern="^filter_"))
    dp.add_handler(CallbackQueryHandler(handle_back, pattern="^back$"))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
   