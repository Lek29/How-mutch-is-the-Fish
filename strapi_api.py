import time

import requests

from utils import STRAPI_TOKEN, STRAPI_URL


def delete_cart_item(document_id: str):
    url = f'{STRAPI_URL}/api/cart-items/{document_id}'
    headers = {'Content-Type': 'application/json'}
    if STRAPI_TOKEN:
        headers['Authorization'] = f'Bearer {STRAPI_TOKEN}'
    try:
        resp = requests.delete(url, headers=headers, timeout=10)
        if resp.status_code in (200, 204):
            print(f'[OK] cart-item {document_id} удалён')
            return True, 'Удалено'
        return False, f'Ошибка удаления {resp.status_code}: {resp.text}'
    except Exception as e:
        return False, f'Исключение: {e}'


def add_to_cart(user_id: int, product_document_id: str, quantity: float = 1.0):
    headers = {'Content-Type': 'application/json'}
    if STRAPI_TOKEN:
        headers['Authorization'] = f'Bearer {STRAPI_TOKEN}'
    cart = get_cart_by_user(user_id)
    if not cart:
        cart = create_cart_in_strapi(user_id)
        if not cart:
            return False
    cart_id = cart['id']
    try:
        url = f'{STRAPI_URL}/api/products'
        params = {'filters[documentId][$eq]': product_document_id}
        r = requests.get(url, params=params, headers=headers, timeout=10)
        r.raise_for_status()
        arr = r.json().get('data', [])
        if not arr:
            print('Товар с documentId не найден:', product_document_id)
            return False
        product_id = arr[0]['id']
    except Exception as e:
        print('Ошибка поиска продукта:', e)
        return False
    url = f'{STRAPI_URL}/api/cart-items'
    payload = {
        'data': {
            'cart': cart_id,
            'product': product_id,
            'quantity': quantity
        }
    }
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        return True
    except Exception as e:
        print('Ошибка создания cart-item:', e)
        if hasattr(e, 'response') and e.response is not None:
            print('Ответ:', e.response.text)
        return False


def get_cart_by_user(user_id: int):
    url = f'{STRAPI_URL}/api/carts'
    params = {
        'filters[user_id][$eq]': user_id,
        'populate': 'cart_items.product.image',
        '_t': int(time.time() * 1000)
    }
    headers = {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache',
    }
    if STRAPI_TOKEN:
        headers['Authorization'] = f'Bearer {STRAPI_TOKEN}'
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json().get('data', [])
        return data[0] if data else None
    except Exception as e:
        print('Ошибка получения корзины:', e)
        return None


def create_cart_in_strapi(user_id: int):
    url = f'{STRAPI_URL}/api/carts'
    headers = {'Content-Type': 'application/json'}
    if STRAPI_TOKEN:
        headers['Authorization'] = f'Bearer {STRAPI_TOKEN}'
    payload = {'data': {'user_id': str(user_id)}}
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.json().get('data')
    except Exception as e:
        print('Ошибка создания корзины в Strapi:', e, getattr(e, 'response', None))
        return None
