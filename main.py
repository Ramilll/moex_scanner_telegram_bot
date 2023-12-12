from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    Filters,
    MessageHandler,
    Updater,
)


class StockBot:
    def __init__(self, token):
        self.token = token
        self.mock_stock_database = ["Stock1", "Stock2", "Stock3"]
        self.user_subscriptions = {}

    def start(self, update: Update, context: CallbackContext) -> None:
        keyboard = [
            [KeyboardButton("Мои подписки"), KeyboardButton("Подписаться")],
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        update.message.reply_text(
            "Привет! Чтобы подписаться на акцию, нажмите кнопку 'Подписаться'.",
            reply_markup=reply_markup,
        )

    def subscribe(self, update: Update, context: CallbackContext) -> None:
        update.message.reply_text(
            "Напишите название акции, на которую хотите подписаться:"
        )

    def show_subscriptions(self, update: Update, context: CallbackContext) -> None:
        chat_id = update.message.chat_id
        subscriptions = self.user_subscriptions.get(chat_id, [])
        if subscriptions:
            update.message.reply_text(
                f"Вы подписаны на следующие акции: {', '.join(subscriptions)}"
            )
        else:
            update.message.reply_text("Вы пока не подписаны ни на одну акцию.")

    def check_stock(self, update: Update, context: CallbackContext) -> None:
        user_input = update.message.text
        chat_id = update.message.chat_id
        if user_input == "Мои подписки":
            self.show_subscriptions(update, context)
        elif user_input == "Подписаться":
            self.subscribe(update, context)
        else:
            if user_input in self.mock_stock_database:
                subscriptions = self.user_subscriptions.get(chat_id, [])
                if user_input in subscriptions:
                    update.message.reply_text(f"Вы уже подписаны на акцию {user_input}")
                else:
                    self.user_subscriptions[chat_id] = self.user_subscriptions.get(
                        chat_id, []
                    ) + [user_input]
                    update.message.reply_text(
                        f"Вы успешно подписаны на акцию {user_input}"
                    )
            else:
                update.message.reply_text(
                    "Извините, не можем подписать вас на эту акцию. Проверьте правильность написания названия акции."
                )

    def run(self):
        updater = Updater(self.token, use_context=True)
        dp = updater.dispatcher

        dp.add_handler(CommandHandler("start", self.start))
        dp.add_handler(CommandHandler("subscribe", self.subscribe))
        dp.add_handler(CommandHandler("subscriptions", self.show_subscriptions))
        dp.add_handler(
            MessageHandler(Filters.text & ~Filters.command, self.check_stock)
        )

        updater.start_polling()
        updater.idle()


if __name__ == "__main__":
    token = "6774933123:AAE4fbID1LhzJY4vJiTGoaHG17mM7tGXHwc"
    bot = StockBot(token)
    bot.run()
