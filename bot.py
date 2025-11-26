import sys
import traceback

from telegram.ext import (CallbackQueryHandler, CommandHandler, Filters,
                          MessageHandler, Updater)

from telegram.error import TelegramError, Unauthorized

from handlers import (handle_add_to_cart, handle_back, handle_menu,
                      handle_message, handle_pay, handle_remove_item,
                      handle_show_cart, handle_to_menu, start)
from utils import get_tg_token


def global_error_handler(update, context):
    print("Необработанная ошибка в handler:", file=sys.stderr)
    traceback.print_exception(type(context.error), context.error, context.error.__traceback__)


def main():
    tg_token = get_tg_token()

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

    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    dp.add_handler(CallbackQueryHandler(handle_remove_item, pattern=r'^remove_.+$'))
    dp.add_handler(CallbackQueryHandler(handle_to_menu, pattern=r'^to_menu$'))
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CallbackQueryHandler(handle_add_to_cart, pattern=r'^add_'))
    dp.add_handler(CallbackQueryHandler(handle_back, pattern='^back$'))
    dp.add_handler(CallbackQueryHandler(handle_show_cart, pattern='^cart$'))
    dp.add_handler(CallbackQueryHandler(handle_pay, pattern=r'^pay$'))
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
