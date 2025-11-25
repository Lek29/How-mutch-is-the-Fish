from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler,Filters
from utils import tg_token
from handlers import start, handle_menu, handle_add_to_cart, handle_back, handle_show_cart, handle_remove_item, \
    handle_to_menu, handle_pay, handle_message


def main():
    updater = Updater(tg_token)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    dp.add_handler(CallbackQueryHandler(handle_remove_item, pattern=r"^remove_.+$"))
    dp.add_handler(CallbackQueryHandler(handle_to_menu, pattern=r"^to_menu$"))
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(handle_add_to_cart, pattern=r"^add_"))
    dp.add_handler(CallbackQueryHandler(handle_back, pattern="^back$"))
    dp.add_handler(CallbackQueryHandler(handle_show_cart, pattern="^cart$"))
    dp.add_handler(CallbackQueryHandler(handle_pay, pattern=r"^pay$"))
    dp.add_handler(CallbackQueryHandler(handle_menu))
    print("Бот запущен с товарами из Strapi")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()