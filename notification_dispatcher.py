from crypto_prices_manager import CryptoPricesManager
from subscription_enum_result import (
    SubscriptionUserToCryptoResult,
    UnsubscriptionUserFromCryptoResult,
)
from subscriptions_manager import SubscriptionsManager


class NotificationDispatcher:
    def __init__(self) -> None:
        self.crypto_prices_manager = CryptoPricesManager()
        self.subscriptions_manager = SubscriptionsManager()

        self._initial_update()

    def _initial_update(self):
        self.crypto_prices_manager.update_all_crypto()
        self.last_crypto_prices = self.crypto_prices_manager.get_crypto_prices()

    def update(self):
        pass
        # TODO(rnazmeev): send notifications about price changes

    def subscribe_user_to_crypto(
        self, user_id: int, crypto_symbol: str
    ) -> SubscriptionUserToCryptoResult:
        return self.subscriptions_manager.subscribe_user_to_crypto(
            user_id, crypto_symbol
        )

    def unsubscribe_user_from_crypto(
        self, user_id: int, crypto_symbol: str
    ) -> UnsubscriptionUserFromCryptoResult:
        return self.subscriptions_manager.unsubscribe_user_to_crypto(
            user_id, crypto_symbol
        )

    def symbol_exists(self, crypto_symbol: str) -> bool:
        return self.crypto_prices_manager.symbol_exists(crypto_symbol)

    def get_last_crypto_price(self, crypto_symbol: str):
        return self.last_crypto_prices[crypto_symbol]

    def get_user_subscriptions(self, user_id: int):
        return self.subscriptions_manager.get_user_subscriptions(user_id)
