import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def edit_message(query, text, reply_markup=None):
    if getattr(query.message, 'photo', None) or getattr(query.message, 'caption', None):
        return query.edit_message_caption(caption=text, reply_markup=reply_markup)
    return query.edit_message_text(text=text, reply_markup=reply_markup)


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


def build_products_menu(strapi_url, strapi_token):
    headers = {'Content-Type': 'application/json'}
    if strapi_token:
        headers['Authorization'] = f'Bearer {strapi_token}'

    url = f'{strapi_url}/api/products'
    params = {'pagination[pageSize]': 100}
    resp = requests.get(url, params=params, headers=headers)
    resp.raise_for_status()
    products = resp.json().get("data", [])

    keyboard = []
    for product in products:
        doc_id = product.get("documentId")
        title = product.get("title", "Без названия")
        keyboard.append([InlineKeyboardButton(title, callback_data=f"add_{doc_id}")])

    return InlineKeyboardMarkup(keyboard)

