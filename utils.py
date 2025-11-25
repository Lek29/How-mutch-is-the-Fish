import redis
from environs import Env
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

env = Env()
env.read_env('.env')

tg_token = env.str('BOT_TOKEN')
STRAPI_URL = env.str('STRAPI_URL', 'http://localhost:1337')
STRAPI_TOKEN = env.str('STRAPI_TOKEN', '')

r = redis.Redis(host='localhost', port=6379, db=0)

def edit_or_send(query, context, text, reply_markup=None):
    try:
        if getattr(query.message, "photo", None) or getattr(query.message, "caption", None):
            query.edit_message_caption(caption=text, reply_markup=reply_markup)
        else:
            query.edit_message_text(text=text, reply_markup=reply_markup)
    except Exception:
        try:
            context.bot.send_message(chat_id=query.message.chat_id, text=text, reply_markup=reply_markup)
        except Exception as e:
            print("Ошибка отправки сообщения в _edit_or_send:", e)

def build_products_keyboard(products, include_cart_button=False):
    keyboard = []

    for product in products:
        keyboard.append([
            InlineKeyboardButton(
                product.get("title", "Без имени"),
                callback_data=product.get("documentId")
            )
        ])

    if include_cart_button:
        keyboard.append([
            InlineKeyboardButton("🛒 Моя корзина", callback_data="cart")
        ])

    return InlineKeyboardMarkup(keyboard)