from enum import Enum
from typing import Dict, List
import yfinance as yf
from sqlalchemy import Column, Float, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from crypto_prices_manager import CryptoPricesManager

import asyncio

from coinmarketcap_fetcher import CoinmarketcapPriceFetcher

Base = declarative_base()

API_KEY = "584680a2-ae47-489b-82b7-4c3d35b5f17b"


class CryptoPrice(Base):
    __tablename__ = "crypto_prices"

    id = Column(Integer, primary_key=True)
    symbol = Column(String, unique=True, nullable=False)
    current_price = Column(Float, default=0.00)


class SubscriptionUserToCryptoResult(Enum):
    Ok = 1
    NoSuchCrypto = 2
    AlreadySubscribed = 3


class UnsubscriptionUserToCryptoResult(Enum):
    Ok = 1
    NotSubscribed = 2


class UserSubscription(Base):
    # Определение таблицы для подписок пользователей
    __tablename__ = "user_subscriptions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    crypto_symbol = Column(String, nullable=False)


class NotificationDispatcher:
    class SubscriptionsManager:
        def __init__(self, database_url="sqlite:///subscription_data.db"):
            # Инициализация менеджера подписок с указанием базы данных
            self.engine = create_engine(
                database_url, echo=True, connect_args={"check_same_thread": False}
            )
            self.Session = sessionmaker(bind=self.engine)
            self._create_tables()

        def _create_tables(self) -> None:
            # Создание необходимых таблиц в базе данных
            Base.metadata.create_all(self.engine, checkfirst=True)
            self._crypto_manager = CryptoPricesManager()

        async def subscribe_user_to_crypto(
            self, user_id: int, crypto_symbol: str
        ) -> SubscriptionUserToCryptoResult:
            session = self.Session()
            try:
                if not self._crypto_manager.crypto_exists(crypto_symbol):
                    return SubscriptionUserToCryptoResult.NoSuchCrypto

                existing_subscription = (
                    session.query(UserSubscription)
                    .filter_by(user_id=user_id, crypto_symbol=crypto_symbol)
                    .first()
                )
                if existing_subscription:
                    return SubscriptionUserToCryptoResult.AlreadySubscribed

                # Подписываем пользователя
                subscription = UserSubscription(
                    user_id=user_id, crypto_symbol=crypto_symbol
                )
                session.merge(subscription)
                session.commit()
                return SubscriptionUserToCryptoResult.Ok

            finally:
                session.close()
                return SubscriptionUserToCryptoResult.Ok

        # Отмена подписки пользователя на акцию
        def unsubscribe_user_from_crypto(
            self, user_id: int, crypto_symbol: str
        ) -> UnsubscriptionUserToCryptoResult:
            session = self.Session()
            try:
                subscription = (
                    session.query(UserSubscription)
                    .filter_by(user_id=user_id, crypto_symbol=crypto_symbol)
                    .first()
                )
                if not subscription:
                    return UnsubscriptionUserToCryptoResult.NotSubscribed
                # Отмена подписки пользователя на акцию
                session.query(UserSubscription).filter_by(
                    user_id=user_id, crypto_symbol=crypto_symbol
                ).delete()
                session.commit()
                return UnsubscriptionUserToCryptoResult.Ok

            finally:
                session.close()
                return UnsubscriptionUserToCryptoResult.Ok

        # Получение списка акций, на которые подписан пользователь
        def get_user_subscriptions(self, user_id: int) -> List[str]:
            session = self.Session()
            try:
                subscriptions = [
                    sub.crypto_symbol
                    for sub in session.query(UserSubscription)
                    .filter_by(user_id=user_id)
                    .all()
                ]
                return [str(symbol) for symbol in subscriptions]
            finally:
                session.close()

        # Получить подписку всех пользователей на какую-то акцию
        def get_all_subscribed_users_to_crypto(self, crypto_symbol: str) -> List[int]:
            session = self.Session()
            try:
                # Для извлечения ид пользователей
                users = [
                    sub.user_id
                    for sub in session.query(UserSubscription.user_id)
                    .filter_by(crypto_symbol=crypto_symbol)
                    .all()
                ]
                return users
            finally:
                session.close()

    class CryptoPricesManager:
        def __init__(
            self, database_url="sqlite:///crypto_prices.db", interval_seconds=60
        ):
            self.engine = create_engine(
                database_url, echo=True, connect_args={"check_same_thread": False}
            )
            self.Session = sessionmaker(bind=self.engine)
            self._create_tables()
            self.crypto_fetcher = CoinmarketcapPriceFetcher(
                api_key=API_KEY, num_fetch_coins=200
            )
            self.interval_seconds = interval_seconds
            self.cnt_update_all_crypto_calls = 0
            self._last_cnt_update_all_crypto_calls = None

        def _create_tables(self):
            Base.metadata.create_all(self.engine, checkfirst=True)

        # Можно через метод start_update_all_crypto асинхронно обновляет цены тикеров
        def start_update_all_crypto(self):
            asyncio.create_task(self.update_all_crypto())

        # Обновляет цены всех акции на таблице crypto_prices
        async def update_all_crypto(self):
            while True:
                try:
                    price_by_symbol = self.crypto_fetcher.fetch_top_coins_prices()
                    for symbol in price_by_symbol:
                        self.add_crypto_price(symbol, price_by_symbol[symbol])
                    self.cnt_update_all_crypto_calls += 1

                except Exception as e:
                    print(f"Error updating crypto prices: {e}")

                # Ждет на interval_seconds секунд
                await asyncio.sleep(self.interval_seconds)

        # Получает все названий тикеров
        def get_all_crypto_symbols(self) -> Set[str]:
            return self.get_crypto_prices().keys()

        # Проверяет, существует ли тикер в бд
        def crypto_exists(self, symbol: str) -> bool:
            return symbol in self.get_all_crypto_symbols()

        # Получает цены всех тикеров
        def get_crypto_prices(self) -> Dict[str, float]:
            # if nothing is updated, return the last price_by_symbol
            if (
                self._last_cnt_update_all_crypto_calls
                == self.cnt_update_all_crypto_calls
            ):
                return self._last_price_by_symbol

            session = self.Session()
            try:
                price_by_symbol = {
                    crypto.symbol: crypto.current_price
                    for crypto in session.query(CryptoPrice).all()
                }
                self._last_price_by_symbol = price_by_symbol
                self._last_cnt_update_all_crypto_calls = (
                    self.cnt_update_all_crypto_calls
                )
                return price_by_symbol
            finally:
                session.close()

        # Добавляет цену тикера
        def add_crypto_price(self, symbol: str, current_price: float):
            session = self.Session()
            try:
                # Проверить, существует ли уже тикер
                existing_crypto = (
                    session.query(CryptoPrice).filter_by(symbol=symbol).first()
                )

                if existing_crypto:
                    # Если тикер существует, обновите ее текущую цену
                    existing_crypto.current_price = current_price
                else:
                    # Если тикер не существует, добавляет его в таблицу
                    crypto = CryptoPrice(symbol=symbol, current_price=current_price)
                    session.add(crypto)

                session.commit()
            finally:
                session.close()
