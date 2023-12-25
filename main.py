import datetime
import logging

from telegram import Update
from telegram.ext import CallbackContext, CommandHandler, Updater

from notification_dispatcher import NotificationDispatcher
from subscriptions_manager import (
    SubscriptionUserToCryptoResult,
    UnsubscriptionUserFromCryptoResult,
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
        self.notification_dispatcher = NotificationDispatcher()
        self.kHelpText = """Вот что я умею:\n
        /subscribe <имена-токенов> <через-пробел> – подписаться на токены <имена-токенов> <через-пробел>. Если Вы уже подписаны на такие токены, повторно мы Вас подписывать не будем.\n
        /unsubscribe <имена-токенов> <через-пробел> – отписаться от токены <имена-токенов> <через-пробел>. Если Вы на какие-то из них не подписаны, мы сообщим Вам об этом.\n
        /my_crypto - вывод списка токенов, на которые Вы подписаны.\n
        /help - вывод этого сообщения.
        """

    def start(self, update: Update, context: CallbackContext) -> None:
        context.chat_data["chat_id"] = update.message.chat_id
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Привет! Я лучший бот-помощник по токенам CoinMarketCap! "
            + self.kHelpText,
        )
        self.schedule_job(context)

    def schedule_job(self, context: CallbackContext) -> None:
        chat_id = context.chat_data.get("chat_id")
        context.job_queue.run_repeating(
            self.run_update, datetime.timedelta(seconds=10), context=chat_id
        )

    def help(self, update: Update, context: CallbackContext) -> None:
        context.bot.send_message(chat_id=update.effective_chat.id, text=self.kHelpText)

    def subscribe(self, update: Update, context: CallbackContext) -> None:
        chat_id = update.effective_chat.id
        if not context.args:
            context.bot.send_message(
                chat_id=chat_id,
                text="Вы не указали имена токенов, на которые хотите подписаться.",
            )
            context.bot.send_message(
                chat_id=chat_id,
                text="Пожалуйста, отправьте сообщение в формате: /subscribe <имена-токенов> <через-пробел>",
            )
            return

        for crypto_name in context.args:
            subscription_result = self.notification_dispatcher.subscribe_user_to_crypto(
                chat_id, crypto_name
            )
            match subscription_result:
                case SubscriptionUserToCryptoResult.NoSuchCrypto:
                    context.bot.send_message(
                        chat_id=chat_id,
                        text="К сожалению, мы не следим за токеном {}.".format(
                            crypto_name
                        ),
                    )
                case SubscriptionUserToCryptoResult.AlreadySubscribed:
                    context.bot.send_message(
                        chat_id=chat_id,
                        text="Вы уже подписаны на токен {}.".format(crypto_name),
                    )
                case SubscriptionUserToCryptoResult.Ok:
                    current_crypto_price = (
                        self.notification_dispatcher.init_subscription_get_price(
                            chat_id, crypto_name
                        )
                    )
                    context.bot.send_message(
                        chat_id=chat_id,
                        text="Подписали Вас на токен {}, текущая цена - {}.".format(
                            crypto_name, current_crypto_price
                        ),
                    )

    def unsubscribe(self, update: Update, context: CallbackContext) -> None:
        chat_id = update.effective_chat.id
        if not context.args:
            context.bot.send_message(
                chat_id=chat_id,
                text="Вы не указали имена токенов, от которых хотите отписаться.",
            )
            context.bot.send_message(
                chat_id=chat_id,
                text="Пожалуйста, отправьте сообщение в формате: /unsubscribe <имена-токенов> <через-пробел>",
            )
            return

        for crypto_name in context.args:
            unsubscription_result = (
                self.notification_dispatcher.unsubscribe_user_from_crypto(
                    chat_id, crypto_name
                )
            )
            match unsubscription_result:
                case UnsubscriptionUserFromCryptoResult.NotSubscribed:
                    context.bot.send_message(
                        chat_id=chat_id,
                        text="Вы не подписаны на токен {}.".format(crypto_name),
                    )
                case UnsubscriptionUserFromCryptoResult.Ok:
                    context.bot.send_message(
                        chat_id=chat_id,
                        text="Отписали Вас от токена {}.".format(crypto_name),
                    )

    def my_crypto(self, update: Update, context: CallbackContext) -> None:
        chat_id = update.message.chat_id
        subscriptions = self.notification_dispatcher.get_user_subscriptions(chat_id)
        if subscriptions:
            context.bot.send_message(
                chat_id=chat_id,
                text="Вы подписаны на токены: {}".format(", ".join(subscriptions)),
            )
        else:
            context.bot.send_message(
                chat_id=chat_id, text="Вы пока не подписаны ни на один токен."
            )

    def run_update(self, context: CallbackContext) -> None:
        notification_updates = self.notification_dispatcher.update()
        for update in notification_updates:
            print(
                f"Update for user_id={update.user_id}, symbol={update.symbol_name}, last_sent_price={update.last_sent_price}, cur_price={update.cur_price}, pct_change={update.pct_change}"
            )

        for update in notification_updates:
            context.bot.send_message(
                chat_id=update.user_id,
                text="Цена на токен {} была {}, стала {}. Поменялась на {}%".format(
                    update.symbol_name,
                    update.last_sent_price,
                    update.cur_price,
                    update.pct_change,
                ),
            )

    def run(self):
        updater = Updater(self.token, use_context=True)
        dp = updater.dispatcher

        dp.add_handler(CommandHandler("start", self.start))
        dp.add_handler(CommandHandler("help", self.help))
        dp.add_handler(CommandHandler("subscribe", self.subscribe))
        dp.add_handler(CommandHandler("unsubscribe", self.unsubscribe))
        dp.add_handler(CommandHandler("my_crypto", self.my_crypto))

        updater.start_polling()
        updater.idle()


if __name__ == "__main__":
    bot = CryptoBot(TOKEN)
    bot.run()
