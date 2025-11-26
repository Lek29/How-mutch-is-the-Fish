import time

import requests

from utils import get_strapi_url, get_strapi_token, get_redis



STRAPI_URL = get_strapi_url()
STRAPI_TOKEN = get_strapi_token()
redis = get_redis()


def delete_cart_item(document_id: str):
    url = f'{STRAPI_URL}/api/cart-items/{document_id}'
    headers = {'Content-Type': 'application/json'}
    if STRAPI_TOKEN:
        headers['Authorization'] = f'Bearer {STRAPI_TOKEN}'
    resp = requests.delete(url, headers=headers, timeout=10)
    resp.raise_for_status()  # выброс исключения на неуспех

    if resp.status_code in (200, 204):
        return True, 'Удалено'

    return False, f'Ошибка удаления: {resp.status_code} {resp.text}'


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
    url = f'{STRAPI_URL}/api/products'
    params = {'filters[documentId][$eq]': product_document_id}
    response = requests.get(url, params=params, headers=headers, timeout=10)
    response.raise_for_status()

    arr = response.json().get('data', [])
    if not arr:
        raise LookupError(f'Товар с documentId {product_document_id} не найден')

    product_id = arr[0]['id']

    url = f'{STRAPI_URL}/api/cart-items'
    payload = {
        'data': {'cart': cart_id, 'product': product_id, 'quantity': quantity}
    }

    resp = requests.post(url, json=payload, headers=headers, timeout=10)
    resp.raise_for_status()

    return True


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

    resp = requests.get(url, params=params, headers=headers, timeout=10)
    resp.raise_for_status()
    carts = resp.json().get('data', [])
    return carts[0] if carts else None


def create_cart_in_strapi(user_id: int):
    url = f'{STRAPI_URL}/api/carts'
    headers = {'Content-Type': 'application/json'}
    if STRAPI_TOKEN:
        headers['Authorization'] = f'Bearer {STRAPI_TOKEN}'
    payload = {'data': {'user_id': str(user_id)}}
    resp = requests.post(url, json=payload, headers=headers, timeout=10)
    resp.raise_for_status()

    return resp.json().get('data')