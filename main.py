import logging

from telegram import Update
from telegram.ext import CallbackContext, CommandHandler, Updater


from notification_dispatcher import (
    NotificationDispatcher,
    SubscriptionUserToCryptoResult,
    UnsubscriptionUserToCryptoResult,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

TOKEN = "6738600960:AAGrtayAHkcjUr74HnNB_L4wc4oR0z2bydY"


class CryptoBot:
    def __init__(self, token):
        self.token = token
        self.mock_crypto_database = ["Crypto1", "Crypto2", "Crypto3"]
        self.user_subscriptions: dict[str, set[str]] = {}
        self.subscriptions_manager = NotificationDispatcher.SubscriptionsManager()
        self.kHelpText = """Вот что я умею:\n
        /subscribe <имена-акций> <через-пробел> – подписаться на акции <имена-акций> <через-пробел>. Если Вы уже подписаны на такие акции, повторно мы Вас подписывать не будем.\n
        /unsubscribe <имена-акций> <через-пробел> – отписаться от акции <имена-акций> <через-пробел>. Если Вы на какие-то из не подписаны, мы сообщим Вам об этом.\n
        /my_crypto - вывод списка акций, на которые Вы подписаны.\n
        /crypto_info <имя-акции> - Рамиль расскажет что тут будет.\n
        /help - вывод этого сообщения.
        """

    def start(self, update: Update, context: CallbackContext) -> None:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Привет! Я лучший бот-помощник по акциям Yahoo! Finance. "
            + self.kHelpText,
        )

    def help(self, update: Update, context: CallbackContext) -> None:
        context.bot.send_message(chat_id=update.effective_chat.id, text=self.kHelpText)

    def subscribe(self, update: Update, context: CallbackContext) -> None:
        chat_id = update.effective_chat.id
        if not context.args:
            context.bot.send_message(
                chat_id=chat_id,
                text="Вы не указали имя акций, на которые хотите подписаться.",
            )
            context.bot.send_message(
                chat_id=chat_id,
                text="Пожалуйста, отправьте сообщение в формате: /subscribe <имена-акций> <через-пробел>",
            )
            return

        for crypto_name in context.args:
            subscription_result = self.subscriptions_manager.subscribe_user_to_crypto(
                chat_id, crypto_name
            )
            match subscription_result:
                case SubscriptionUserToCryptoResult.NoSuchCrypto:
                    context.bot.send_message(
                        chat_id=chat_id,
                        text="К сожалению, мы не следим за акцией {}.".format(
                            crypto_name
                        ),
                    )
                case SubscriptionUserToCryptoResult.AlreadySubscribed:
                    context.bot.send_message(
                        chat_id=chat_id,
                        text="Вы уже подписаны на акцию {}.".format(crypto_name),
                    )
                case SubscriptionUserToCryptoResult.Ok:
                    self.user_subscriptions[chat_id].add(crypto_name)
                    context.bot.send_message(
                        chat_id=chat_id,
                        text="Подписали Вас на акцию {}.".format(crypto_name),
                    )

    def unsubscribe(self, update: Update, context: CallbackContext) -> None:
        chat_id = update.effective_chat.id
        if not context.args:
            context.bot.send_message(
                chat_id=chat_id,
                text="Вы не указали имя акций, от которых хотите отписаться.",
            )
            context.bot.send_message(
                chat_id=chat_id,
                text="Пожалуйста, отправьте сообщение в формате: /unsubscribe <имена-акций> <через-пробел>",
            )
            return

        for crypto_name in context.args:
            unsubscription_result = (
                self.subscriptions_manager.unsubscribe_user_to_crypto(
                    chat_id, crypto_name
                )
            )
            match unsubscription_result:
                case UnsubscriptionUserToCryptoResult.NotSubscribed:
                    context.bot.send_message(
                        chat_id=chat_id,
                        text="Вы не подписаны на акцию {}.".format(crypto_name),
                    )
                case UnsubscriptionUserToCryptoResult.Ok:
                    context.bot.send_message(
                        chat_id=chat_id,
                        text="Отписали Вас от акции {}.".format(crypto_name),
                    )

    def my_crypto(self, update: Update, context: CallbackContext) -> None:
        chat_id = update.message.chat_id
        subscriptions = self.subscriptions_manager.get_user_subscriptions(chat_id)
        if subscriptions:
            context.bot.send_message(
                chat_id=chat_id,
                text="Вы подписаны на акции: {}".format(", ".join(subscriptions)),
            )
        else:
            context.bot.send_message(
                chat_id=chat_id, text="Вы пока не подписаны ни на одну акцию."
            )

    def run(self):
        updater = Updater(self.token, use_context=True)
        dp = updater.dispatcher

        dp.add_handler(CommandHandler("start", self.start))
        dp.add_handler(CommandHandler("help", self.help))
        dp.add_handler(CommandHandler("subscribe", self.subscribe))
        dp.add_handler(CommandHandler("unsubscribe", self.unsubscribe))
        dp.add_handler(CommandHandler("my_crypto", self.my_crypto))
        # dp.add_handler(CommandHandler("info", self.info))

        updater.start_polling()
        updater.idle()


if __name__ == "__main__":
    bot = CryptoBot(TOKEN)
    bot.run()
