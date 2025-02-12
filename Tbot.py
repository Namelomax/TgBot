import telebot
from telebot import types
import requests
from bs4 import BeautifulSoup
import re
import chardet
import html

TOKEN = "TGToken"
bot = telebot.TeleBot(TOKEN)

URL_first = "https://www.noob-club.ru/index.php?topic=9598.0"
LOCAL_VK_HTML = "vk.html"

# поиск по сайту
def get_definitionFirst(term):
    response = requests.get(URL_first)
    if response.status_code != 200:
        return "❌ Ошибка доступа к сайту."

    soup = BeautifulSoup(response.text, "html.parser")

    for strong in soup.find_all("strong"):
        if re.search(r'\b' + re.escape(term.lower()) + r'\b', strong.get_text(strip=True).lower()):
            br_tag = strong.find_next("br")
            if br_tag and br_tag.next_sibling:
                definition = br_tag.next_sibling.strip()
                return f"{term.capitalize()}:\n{definition}"

    return None

# поиск по файлу
def get_definition_second(term):
    try:
        with open(LOCAL_VK_HTML, "rb") as file:
            raw_data = file.read()
            encoding = chardet.detect(raw_data)['encoding']
        with open(LOCAL_VK_HTML, "r", encoding=encoding) as file:
            html_content = file.read()
    except FileNotFoundError:
        return "❌ Не удалось найти локальный файл с данными."
    except Exception as e:
        return f"❌ Ошибка при чтении файла: {str(e)}"

    html_content = html.unescape(html_content)

    pattern = r"\b([\w\sА-Яа-яЁё]+?)\s*-\s*([^<]+)\b"
    matches = re.findall(pattern, html_content)

    for term_found, definition in matches:
        if term.lower() in term_found.lower():
            return f"{term_found.strip()}:\n{definition.strip()}"

    return None

def get_definition(term):
    definition = get_definitionFirst(term)
    if definition:
        return definition
    definition = get_definition_second(term)
    if definition:
        return definition

    return "❌ Термин не найден."

@bot.message_handler(commands=['start'])
def start_bot(message):
    text = (f"Привет, {message.from_user.first_name}! Я могу помочь найти термины.\n"
            "✅ Введите команду /search [термин]\n"
            "✅ Или нажмите кнопку «Поиск термина».")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔍 Поиск термина", callback_data="search_term"))
    bot.send_message(message.chat.id, text, reply_markup=markup)

# обработка входящих сообщений
@bot.message_handler()
def send_text(message):
    parts = message.text.split(maxsplit=1)
    print(parts)
    term = parts[0]
    definition = get_definition(term)
    if not definition:
        bot.send_message(message.chat.id, "❌ Ошибка: не удалось найти термин.")
        return
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔍 Искать снова", callback_data="search_term"))
    bot.send_message(message.chat.id, definition, reply_markup=markup)

# обработка кнопки поиска
@bot.message_handler(commands=['search'])
def search_term(message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.send_message(message.chat.id, "❌ Укажите термин: /search [термин]")
        return

    term = parts[1]
    definition = get_definition(term)
    if not definition:
        bot.send_message(message.chat.id, "❌ Ошибка: не удалось найти термин.")
        return

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔍 Искать снова", callback_data="search_term"))
    bot.send_message(message.chat.id, definition, reply_markup=markup)

# обработка команды поиска
@bot.callback_query_handler(func=lambda call: call.data == "search_term")
def ask_for_term(call):
    bot.send_message(call.message.chat.id, "🔍 Введите термин для поиска:")
    bot.register_next_step_handler(call.message, process_search)

def process_search(message):
    term = message.text.strip()
    if not term:
        bot.send_message(message.chat.id, "❌ Введите корректный термин.")
        return

    definition = get_definition(term)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔍 Искать снова", callback_data="search_term"))
    bot.send_message(message.chat.id, definition, reply_markup=markup)

bot.infinity_polling()