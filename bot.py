import sys
import traceback

from environs import Env
from telegram.ext import (CallbackQueryHandler, CommandHandler, Filters,
                          MessageHandler, Updater)

from telegram.error import TelegramError, Unauthorized

from handlers import (handle_add_to_cart, handle_back, handle_menu,
                      handle_message, handle_pay,
                      handle_show_cart, handle_to_menu, start, handle_remove_item)

from functools import partial
from redis import Redis


def global_error_handler(update, context):
    print("Необработанная ошибка в handler:", file=sys.stderr)
    traceback.print_exception(type(context.error), context.error, context.error.__traceback__)


def main():
    env = Env()
    env.read_env('.env')

    tg_token = env.str("TG_BOT_TOKEN")
    strapi_url = env.str("STRAPI_URL", "http://localhost:1337")
    strapi_token = env.str("STRAPI_TOKEN", "")
    # redis_client = create_redis_client()

    redis_client = Redis(
        host = env.str('REDIS_HOST', 'localhost'),
        port = env.int('REDIS_PORT', 6379),
        db = env.int('REDIS_DB', 0),
    )
    try:
        updater = Updater(tg_token)
        bot = updater.bot
        bot.get_me()
        print('Токен корректный, бот запускается...')

    except Unauthorized:
        print('Ошибка: неверный TOKEN Telegram. Проверь переменную окружения.')
        return

    except TelegramError as e:
        print(f'Ошибка при инициализации бота: {e}')
        return

    except Exception as e:
        print(f'Неизвестная ошибка при создании бота: {e}')
        return
    dp = updater.dispatcher

    dp.add_error_handler(global_error_handler)

    dp.add_handler(
        MessageHandler(
            Filters.text & ~Filters.command,
            partial(
                handle_message,
                    redis_client=redis_client,
                    strapi_url=strapi_url,
                    strapi_token=strapi_token)
        )
    )

    dp.add_handler(CallbackQueryHandler(
        partial(
        handle_remove_item,
            strapi_url=strapi_url,
            strapi_token=strapi_token),
        pattern=r'^remove_.+$')
    )
    dp.add_handler(CallbackQueryHandler(handle_to_menu, pattern=r'^to_menu$'))
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CallbackQueryHandler(
        partial(
            handle_add_to_cart,
            strapi_url=strapi_url,
            strapi_token=strapi_token),
        pattern=r'^add_'))
    dp.add_handler(CallbackQueryHandler(handle_back, pattern='^back$'))
    dp.add_handler(CallbackQueryHandler(
        partial(
        handle_show_cart,
            strapi_url=strapi_url,
            strapi_token=strapi_token),
        pattern='^cart$'))
    dp.add_handler(CallbackQueryHandler(
        partial(handle_pay, redis_client=redis_client)
        , pattern=r'^pay$'))
    dp.add_handler(CallbackQueryHandler(handle_menu))

    try:
        updater.start_polling()
        updater.idle()

    except TelegramError as e:
        print(f'Telegram API ошибка: {e}')

    except Exception as e:
        print(f"Фатальная ошибка в основном цикле: {e}")


    updater.idle()


if __name__ == '__main__':
    main()
