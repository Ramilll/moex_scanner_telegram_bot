import logging
from dataclasses import dataclass
from typing import Dict, List

from crypto_prices_manager import CryptoPricesManager
from subscription_enum_result import (
    SubscriptionUserToCryptoResult,
    UnsubscriptionUserFromCryptoResult,
)
from subscriptions_manager import SubscriptionsManager


class SubscrberUpdateResult:
    def __init__(self):
        self.last_sent_price_by_symbol = {}  # Dict[str, float]

    def is_symbol_sent(self, symbol: str):
        return symbol in self.last_sent_price_by_symbol

    def set_last_sent_price(self, symbol: str, price: float):
        self.last_sent_price_by_symbol[symbol] = price

    def get_last_sent_price(self, symbol: str):
        return self.last_sent_price_by_symbol[symbol]


@dataclass
class NotificationUpdate:
    user_id: int
    last_sent_price: float
    cur_price: float
    pct_change: float
    symbol_name: str


class NotificationDispatcher:
    def __init__(self) -> None:
        self.crypto_prices_manager = CryptoPricesManager()
        self.subscriptions_manager = SubscriptionsManager()
        self.update_result_by_user_id = {}  # Dict[int, SubscrberUpdateResult]

        self._initial_update()

        self.MIN_PCT_CHANGE_TO_NOTIFY = 0.01  # (in percents)

    def _initial_update(self) -> None:
        self.crypto_prices_manager.update_all_crypto()

    def get_crypto_symbols(self) -> List[str]:
        return self.crypto_prices_manager.get_crypto_symbols()

    def update(self) -> List[NotificationUpdate]:
        self.crypto_prices_manager.update_all_crypto()

        notifications = []  # List[NotificationUpdate]

        cur_prices_by_symbol = self.crypto_prices_manager.get_crypto_prices()

        for symbol in cur_prices_by_symbol:
            for (
                subscriber_id
            ) in self.subscriptions_manager.get_all_subscribed_users_to_crypto(symbol):
                last_update_result = self.update_result_by_user_id.get(subscriber_id)

                # we expect that last_update_result is not None (user has received )
                if not last_update_result:
                    print(f"Unexpected error for user_id={subscriber_id}")
                    continue

                if not last_update_result.is_symbol_sent(symbol):
                    # we expect that user has subscribed to this symbol
                    print(f"Unexpected error for user_id={subscriber_id}")
                    continue

                last_sent_price = last_update_result.get_last_sent_price(symbol)
                cur_price = cur_prices_by_symbol[symbol]
                pct_change = (cur_price - last_sent_price) / last_sent_price * 100

                if abs(pct_change) >= self.MIN_PCT_CHANGE_TO_NOTIFY:
                    notifications.append(
                        NotificationUpdate(
                            user_id=subscriber_id,
                            last_sent_price=last_sent_price,
                            cur_price=cur_price,
                            pct_change=pct_change,
                            symbol_name=symbol,
                        )
                    )
                    last_update_result.set_last_sent_price(symbol, cur_price)

        return notifications

    def subscribe_user_to_crypto(
        self, user_id: int, crypto_symbol: str
    ) -> SubscriptionUserToCryptoResult:
        return self.subscriptions_manager.subscribe_user_to_crypto(
            user_id, crypto_symbol
        )

    def init_subscription_get_price(self, user_id: int, crypto_symbol: str) -> float:
        # we call this function after subscribe_user_to_crypto was called (if it was successfull)
        last_symbol_price = self.crypto_prices_manager.get_crypto_prices()[
            crypto_symbol
        ]
        # init Update result
        if user_id not in self.update_result_by_user_id:
            self.update_result_by_user_id[user_id] = SubscrberUpdateResult()
        self.update_result_by_user_id[user_id].set_last_sent_price(
            crypto_symbol, last_symbol_price
        )
        return last_symbol_price

    def unsubscribe_user_from_crypto(
        self, user_id: int, crypto_symbol: str
    ) -> UnsubscriptionUserFromCryptoResult:
        return self.subscriptions_manager.unsubscribe_user_from_crypto(
            user_id, crypto_symbol
        )

    def get_user_subscriptions(self, user_id: int):
        return self.subscriptions_manager.get_user_subscriptions(user_id)
