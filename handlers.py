import io

import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import BadRequest
from telegram.ext import CallbackContext

from strapi_api import (STRAPI_TOKEN, STRAPI_URL, add_to_cart,
                        delete_cart_item, get_cart_by_user)
from utils import build_products_keyboard, edit_or_send, r


def handle_message(update: Update, context: CallbackContext):
    from utils import r
    user_id = update.effective_user.id
    state = r.get(user_id)
    if state and state.decode('utf-8') == 'WAITING_EMAIL':
        email = update.message.text
        print(f'Получена почта от пользователя {user_id}: {email}')

        url = f'{STRAPI_URL}/api/clients'
        headers = {'Content-Type': 'application/json'}
        if STRAPI_TOKEN:
            headers['Authorization'] = f'Bearer {STRAPI_TOKEN}'
        payload = {'data': {'email': email}}
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            resp.raise_for_status()
            print(f'Клиент создан в Strapi: ID {resp.json()["data"]["id"]}')
            update.message.reply_text(f'Ваша почта {email} получена и сохранена. Мы свяжемся с вами!')
        except Exception as e:
            print(f'Ошибка создания клиента: {e}')
            update.message.reply_text('Ошибка сохранения почты. Попробуйте позже.')
        r.delete(user_id)
    else:
        update.message.reply_text('Я не понимаю это сообщение. Используйте меню.')

def handle_pay(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    r.set(query.from_user.id, 'WAITING_EMAIL')
    query.edit_message_text('Введите вашу почту для оформления заказа.')


def handle_show_cart(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    cart = get_cart_by_user(user_id)
    if not cart:
        edit_or_send(query, context, 'У вас пока нет корзины или она пустая.')
        return

    cart_items = cart.get('cart_items', [])

    if not cart_items or len(cart_items) == 0:
        edit_or_send(query, context, 'Ваша корзина пустая.')
        return

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
    edit_or_send(query, context, text, reply_markup)


def handle_remove_item(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    data = query.data
    try:
        _, item_id_str = data.split("_", 1)
        item_id = item_id_str
    except Exception:
        try:
            query.edit_message_text('Некорректный идентификатор для удаления.')
        except Exception:
            context.bot.send_message(chat_id=query.message.chat_id, text='Некорректный идентификатор для удаления.')
        return
    success, msg = delete_cart_item(item_id)
    if not success:
        print(f'Ошибка при удалении cart-item {item_id}: {msg}')
        try:
            query.edit_message_text('Не удалось удалить позицию: ' + msg)
        except Exception:
            context.bot.send_message(chat_id=query.message.chat_id, text='Не удалось удалить позицию: ' + msg)
        return
    handle_show_cart(update, context)


def handle_add_to_cart(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    document_id = query.data[len('add_'):]
    success = add_to_cart(user_id, document_id, 1.0)
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
    query = update.callback_query
    try:
        query.answer()
    except BadRequest as e:
        if 'query is too old' in str(e):
            pass
        else:
            raise
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
    print(f'Пользователь: {user_id}')
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
        query.edit_message_text('Товар не найден.')
        return
    title = product.get('title', '')
    description = product.get('description', '')
    price = product.get('price', '')
    image_url = None
    image = product.get('image')
    if image and image.get('url'):
        image_url = 'http://localhost:1337' + image['url']
    caption = f'*{title}*\n\n{description}\n\n *Цена:* {price} ₽'
    keyboard = [
        [InlineKeyboardButton('В корзину', callback_data=f'add_{document_id}')],
        [InlineKeyboardButton('К списку', callback_data='back')],
        [InlineKeyboardButton('Моя корзина', callback_data='cart')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    try:
        context.bot.delete_message(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id
        )
    except Exception as e:
        print('Delete error:', e)
    if image_url:
        try:
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
        except Exception as e:
            print('Ошибка загрузки фото:', e)
            context.bot.send_message(
                chat_id=query.message.chat_id,
                text=caption + '\n\n_Картинка не загрузилась_',
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
    try:
        context.bot.delete_message(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id
        )
    except Exception as e:
        print('Не удалось удалить сообщение:', e)
    start(update, context)


def get_products():
    url = 'http://localhost:1337/api/products'
    params = {
        'populate': 'image'
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()['data']
    except Exception as e:
        print('Ошибка API:', e)
        return []


def get_product_by_id(document_id):
    url = f'http://localhost:1337/api/products/{document_id}'
    params = {'populate': 'image'}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()['data']
    except Exception as e:
        print('Ошибка товара:', e)
        return None
