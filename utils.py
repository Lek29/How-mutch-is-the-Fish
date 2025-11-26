import redis
from environs import Env
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_env():
    env = Env()
    env.read_env('.env')
    return env


def get_tg_token():
    return get_env().str('TG_BOT_TOKEN')


def get_strapi_url():
    return get_env().str('STRAPI_URL', 'http://localhost:1337')


def get_strapi_token():
    return get_env().str('STRAPI_TOKEN', '')


def get_redis():
    env = get_env()

    REDIS_HOST = env.str('REDIS_HOST', 'localhost')
    REDIS_PORT = env.int('REDIS_PORT', 6379)
    REDIS_DB = env.int('REDIS_DB', 0)

    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)


def edit_message(query, text, reply_markup=None):
    if getattr(query.message, 'photo', None) or getattr(query.message, 'caption', None):
        return query.edit_message_caption(caption=text, reply_markup=reply_markup)
    return query.edit_message_text(text=text, reply_markup=reply_markup)


def send_message(bot, chat_id, text, reply_markup=None):
    return bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)


def build_products_keyboard(products, include_cart_button=False):
    keyboard = []

    for product in products:
        keyboard.append([
            InlineKeyboardButton(
                product.get('title', 'Без имени'),
                callback_data=product.get('documentId')
            )
        ])

    if include_cart_button:
        keyboard.append([
            InlineKeyboardButton('Моя корзина', callback_data='cart')
        ])
    return InlineKeyboardMarkup(keyboard)
