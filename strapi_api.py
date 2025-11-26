import time

import requests


def delete_cart_item(document_id: str,  strapi_url: str, strapi_token: str):
    url = f'{strapi_url}/api/cart-items/{document_id}'
    headers = {'Content-Type': 'application/json'}
    if strapi_token:
        headers['Authorization'] = f'Bearer {strapi_token}'
    resp = requests.delete(url, headers=headers, timeout=10)
    resp.raise_for_status()

    if resp.ok:
        return True

    return False, f'Ошибка удаления: {resp.status_code} {resp.text}'


def add_to_cart(user_id: int, product_document_id: str, quantity: float, strapi_url=None, strapi_token=None):
    print(f'This is documentId : {product_document_id}')
    headers = {'Content-Type': 'application/json'}
    if strapi_token:
        headers['Authorization'] = f'Bearer {strapi_token}'
    cart = get_cart_by_user(user_id, strapi_url=strapi_url, strapi_token=strapi_token)
    if not cart:
        cart = create_cart_in_strapi(user_id, strapi_url=strapi_url, strapi_token=strapi_token)
        if not cart:
            return False
    cart_id = cart['id']
    url = f'{strapi_url}/api/products'
    params = {'filters[documentId][$eq]': product_document_id}
    response = requests.get(url, params=params, headers=headers, timeout=10)
    response.raise_for_status()

    arr = response.json().get('data', [])
    if not arr:
        print("Ответ Strapi при поиске продукта:", response.json())
        raise LookupError(f'Товар с documentId {product_document_id} не найден')

    product_id = arr[0]['id']

    url = f'{strapi_url}/api/cart-items'
    payload = {
        'data': {'cart': cart_id, 'product': product_id, 'quantity': quantity}
    }

    resp = requests.post(url, json=payload, headers=headers, timeout=10)
    resp.raise_for_status()

    return True


def get_cart_by_user(user_id: int, strapi_url: str, strapi_token: str):
    url = f'{strapi_url}/api/carts'
    params = {
        'filters[user_id][$eq]': user_id,
        'populate': 'cart_items.product.image',
        '_t': int(time.time() * 1000)
    }
    headers = {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache',
    }
    if strapi_token:
        headers['Authorization'] = f'Bearer {strapi_token}'

    resp = requests.get(url, params=params, headers=headers, timeout=10)
    resp.raise_for_status()
    carts = resp.json().get('data', [])
    return carts[0] if carts else None


def create_cart_in_strapi(user_id: int, strapi_url: str, strapi_token: str):
    url = f'{strapi_url}/api/carts'
    headers = {'Content-Type': 'application/json'}
    if strapi_token:
        headers['Authorization'] = f'Bearer {strapi_token}'
    payload = {'data': {'user_id': str(user_id)}}
    resp = requests.post(url, json=payload, headers=headers, timeout=10)
    resp.raise_for_status()

    return resp.json().get('data')