import io

import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update

from telegram.ext import CallbackContext

from strapi_api import (add_to_cart,
                        delete_cart_item, get_cart_by_user, create_cart_in_strapi)
from utils import edit_message, build_products_keyboard


def handle_message(update: Update, context: CallbackContext, redis_client, strapi_url: str, strapi_token: str):
    user_id = update.effective_user.id
    state = redis_client.get(user_id)
    if state and state.decode('utf-8') == 'WAITING_EMAIL':
        email = update.message.text
        url = f'{strapi_url}/api/clients'
        headers = {'Content-Type': 'application/json'}
        if strapi_token:
            headers['Authorization'] = f'Bearer {strapi_token}'
        payload = {'data': {'email': email}}
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        resp.raise_for_status()

        client_id = resp.json()['data']['id']

        update.message.reply_text(
            f'Ваша почта {email} получена и сохранена. Мы свяжемся с вами!'
        )


def handle_pay(update: Update, context: CallbackContext, redis_client):
    query = update.callback_query
    query.answer()
    redis_client.set(query.from_user.id, 'WAITING_EMAIL')

    query.edit_message_caption(
        caption='Введите вашу почту для оформления заказа.',
        reply_markup=None
    )


def handle_show_cart(update: Update, context: CallbackContext, strapi_url: str, strapi_token: str):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    cart = get_cart_by_user(user_id, strapi_url=strapi_url, strapi_token=strapi_token)
    if not cart:
        return context.bot.send_message(
            chat_id=query.message.chat_id,
            text='У вас пока нет корзины или она пустая.'
        )

    cart_items = cart.get('cart_items', [])

    if not cart_items or len(cart_items) == 0:
        return context.bot.send_message(
            chat_id=query.message.chat_id,
            text='Ваша корзина пустая.'
        )

    lines = ['Ваша корзина:\n']
    keyboard = []
    total = 0.0

    for idx, item in enumerate(cart_items, start=1):
        cart_item_id = item.get('id')
        cart_item_document_id = item.get('documentId')
        if not cart_item_id or not cart_item_document_id:
            continue

        quantity = float(item.get('quantity', 0) or 0)
        product = item.get('product', {})

        title = product.get('title', 'Без названия')
        price = float(product.get('price', 0) or 0)
        subtotal = price * quantity
        total += subtotal

        lines.append(f'{idx}. {title} — {quantity} кг × {price} ₽ = {subtotal:.2f} ₽')
        keyboard.append([InlineKeyboardButton(f'Удалить {idx}', callback_data=f'remove_{cart_item_document_id}')])

    lines.append(f'\nИтого: {total:.2f} ₽')
    keyboard.append([InlineKeyboardButton(' В меню', callback_data='to_menu')])
    keyboard.append([InlineKeyboardButton('Оплатить', callback_data='pay')])

    text = "\n".join(lines)
    reply_markup = InlineKeyboardMarkup(keyboard)
    edit_message(query, text, reply_markup)


def handle_remove_item(update: Update, context: CallbackContext, strapi_url, strapi_token):
    query = update.callback_query
    query.answer()

    _, item_id = query.data.split("_", 1)

    success = delete_cart_item(
        item_id,
        strapi_url=strapi_url,
        strapi_token=strapi_token
    )
    query.edit_message_caption(
        caption="Товар удалён!",
        reply_markup=None
    )

    if not success:
        raise RuntimeError("Ошибка удаления")

    return handle_show_cart(update, context, strapi_url=strapi_url, strapi_token=strapi_token)


def handle_add_to_cart(update: Update, context: CallbackContext, strapi_url, strapi_token):
    query = update.callback_query
    query.answer()

    user_id = query.from_user.id
    product_id = query.data[len('add_'):]

    cart = get_cart_by_user(user_id, strapi_url=strapi_url, strapi_token=strapi_token)

    if not cart:
        cart = create_cart_in_strapi(user_id, strapi_url=strapi_url, strapi_token=strapi_token)

    cart_id = cart["id"]

    success = add_to_cart(
        cart_id,
        product_id,
        1.0,
        strapi_url,
        strapi_token
    )

    if success:
        query.edit_message_caption(
            caption=query.message.caption + '\n\nТовар добавлен в корзину!',
            reply_markup=query.message.reply_markup
        )
    else:
        query.edit_message_caption(
            caption=query.message.caption + '\n\nНе удалось добавить в корзину.',
            reply_markup=query.message.reply_markup
        )


def handle_to_menu(update: Update, context: CallbackContext):
    update.callback_query.answer()
    start(update, context)


def start(update: Update, context: CallbackContext):
    if update.message:
        chat = update.message.chat
        chat_id = update.message.chat_id
        reply_target = update.message
    elif update.callback_query and update.callback_query.message:
        chat = update.callback_query.message.chat
        chat_id = update.callback_query.message.chat_id
        reply_target = None
    else:
        return
    user_id = update.effective_user.id
    products = get_products()
    if not products:
        if reply_target:
            reply_target.reply_text('Ошибка: не удалось загрузить товары.')
        else:
            context.bot.send_message(chat_id=chat_id, text='Ошибка: не удалось загрузить товары.')
        return
    reply_markup = build_products_keyboard(products, include_cart_button=True)
    text = 'Выберите товар:'
    if reply_target:
        reply_target.reply_text(text, reply_markup=reply_markup)
    else:
        context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)

def handle_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    user_id = query.from_user.id
    document_id = query.data

    product = get_product_by_id(document_id)
    if not product:
        raise LookupError("Товар не найден")

    title = product.get('title', '')
    description = product.get('description', '')
    price = product.get('price', '')

    image = product.get('image')
    image_url = None
    if image and image.get('url'):
        image_url = 'http://localhost:1337' + image['url']

    caption = f'*{title}*\n\n{description}\n\n *Цена:* {price} ₽'

    keyboard = [
        [InlineKeyboardButton('В корзину', callback_data=f'add_{document_id}')],
        [InlineKeyboardButton('К списку', callback_data='back')],
        [InlineKeyboardButton('Моя корзина', callback_data='cart')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.delete_message(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id
    )

    if image_url:
        img_response = requests.get(image_url)
        img_response.raise_for_status()

        img_data = io.BytesIO(img_response.content)
        img_data.name = 'product.jpg'

        context.bot.send_photo(
            chat_id=query.message.chat_id,
            photo=img_data,
            caption=caption,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    else:
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text=caption,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )


def handle_back(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    context.bot.delete_message(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id
    )
    start(update, context)


def get_products():
    url = 'http://localhost:1337/api/products'
    params = {'populate': 'image'}

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()

    return response.json()['data']


def get_product_by_id(document_id):
    url = f'http://localhost:1337/api/products/{document_id}'
    params = {'populate': 'image'}

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()

    return response.json()['data']
