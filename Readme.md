# Telegram-Бот Магазина Рыбы
Это Telegram-бот для онлайн-магазина рыбы, интегрированный с `CMS Strapi v5`. Бот позволяет пользователям просматривать продукты, добавлять их в корзину, просматривать корзину, удалять элементы и "оплачивать" путём предоставления адреса электронной почты. Email сохраняется в Strapi как запись "Client" для обработки заказа. Состояния управляются с помощью Redis. Код модулизован в отдельные файлы для лучшей организации: utils.py (утилиты и конфиг), strapi_api.py (работа с API Strapi), handlers.py (обработчики Telegram), bot.py (запуск бота).
Бот использует API Strapi для продуктов, корзины и клиентов. Поддерживает изображения продуктов, расчет суммы, удаление элементов. Для оплаты — запрос email и сохранение в CMS.
## Возможности

* Список продуктов из Strapi с кнопками
* Детали продукта с описанием, ценой и изображением
* Добавление продукта в корзину
* Просмотр корзины с нумерацией, суммой и кнопками удаления
* Удаление элементов из корзины
* Кнопка "Оплатить" для запроса email
* Сохранение email в Strapi как клиента
* Управление состояниями с Redis (для WAITING_EMAIL)
* Безопасное редактирование сообщений (фото или текст)
* Обработка ошибок (например, 404, 403 от Strapi)

## Требования

* Python 3.8 или выше
* Telegram Bot Token (получите от BotFather в Telegram)
* Strapi v5, запущенный на localhost:1337
* API-токен Strapi с правами на чтение/запись коллекций (Product, Cart, CartItem, Client)
* Redis сервер на localhost:6379 (установите Redis, если нет)
* Файл .env с переменными: BOT_TOKEN, STRAPI_URL, STRAPI_TOKEN
* Node.js (LTS версия 18.x или 20.x) и npm для Strapi
* Библиотеки Python: python-telegram-bot, requests, environs, redis

## Установка

1. Клонируйте репозиторий:
```bash
  clone <URL репозитория>
  cd <папка репозитория>
```
2. Установите зависимости Python:
```bash
  pip install -r requirements.txt
```
3. Создайте файл .env в корневой папке с следующим содержимым:
```
TG_BOT_TOKEN=ваш_токен_бота_из_Telegram
STRREDIS_HOST='localhost'
REDIS_PORT=6379
REDIS_DB=0
STRAPI_URL=http://localhost:1337

```
* или внесите ваши настроки.
## Запуск Strapi v5
**Strapi** — CMS для `backend`. Если Strapi не установлен, следуйте шагам:

1. Установите Node.js (скачайте с `nodejs.org`, проверьте: `node --version`).
2. Создайте проект Strapi:
```
    npx create-strapi-app@latest my-strapi-project
```
* Следуйте промптам: выберите шаблон "Quickstart", базу данных SQLite (для простоты), остальные дефолты.

3. Перейдите в папку проекта:
```
   cd my-strapi-project
```
4. Запустите Strapi:
```
npm run develop
```
* Сервер запустится на `http://localhost:1337.`
* Откройте `http://localhost:1337/admin`, зарегистрируйте администратора (email/пароль).

5. Настройте permissions для API-токена:
* В admin panel перейдите в Settings > Users & Roles > Roles.
* Для роли "Authenticated" включите permissions для коллекций: Product (find, findOne), Cart (create, find, update), CartItem (create, delete, find), Client (create, find).
* Создайте API-токен в Settings > API Tokens: Type "Full access" или "Custom" с нужными permissions, скопируйте токен в .env как STRAPI_TOKEN.


## Создание карточек продуктов в Strapi
Карточки продуктов — это записи в коллекции "Product". Если коллекции нет, создайте её.

1. В admin panel перейдите в Content-type Builder > Collection types.
2. Нажмите "Create new collection type".
3. Display name: "Product" (API ID станет "products").
4. Добавьте поля:
* Title: Text (short text).
* Description: Text (long text).
* Price: Number (decimal).
* Image: Media (single image).

5. Save, Strapi перезапустится.
6. В Content Manager > Product создайте записи:
* Заполните title, description, price, загрузите image (jpg/png).
* Publish запись (кнопка Publish).


## Запуск бота

1. Убедитесь, что Redis запущен (в терминале: redis-server, или проверьте 127.0.0.1:6379).
2. Убедитесь, что Strapi запущен (npm run develop).
3. В папке проекта запустите бота:
```
python bot.py
```
* Бот запустится, лог "Бот запущен с товарами из Strapi".

4. В Telegram найдите бота по имени (из BotFather), отправьте /start.

## Тестирование

* /start: Показывает список продуктов.
* Выберите продукт: Детали с изображением.
* "В корзину": Добавляет.
* "Моя корзина": Просмотр, удаление, "Оплатить".
* "Оплатить": Запрос email.
* Введите email: Сохраняется в Strapi (проверьте в Content Manager > Client).
* Проверьте клиента: GET http://localhost:1337/api/clients?filters[email][$eq]=your@email.com (в браузере или Postman).

## Структура файлов

* utils.py: Утилиты, конфиг (.env), Redis, клавиатуры.
* strapi_api.py: Функции API Strapi (GET/POST/DELETE).
* handlers.py: Обработчики Telegram (callback, message).
* bot.py: Запуск бота, регистрация handlers.