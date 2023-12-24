from typing import Dict, List

import yfinance as yf
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from crypto_prices_manager import CryptoPricesManager

Base = declarative_base()


class UserSubscription(Base):
    # Определение таблицы для подписок пользователей
    __tablename__ = "user_subscriptions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    crypto_symbol = Column(String, nullable=False)


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

    def subscribe_user_to_crypto(
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

    # Отмена подписки пользователя на акцию
    def unsubscribe_user_from_crypto(
        self, user_id: int, crypto_symbol: str
    ) -> UnsubscriptionUserFromCryptoResult:
        session = self.Session()
        try:
            subscription = (
                session.query(UserSubscription)
                .filter_by(user_id=user_id, crypto_symbol=crypto_symbol)
                .first()
            )
            if not subscription:
                return UnsubscriptionUserFromCryptoResult.NotSubscribed
            # Отмена подписки пользователя на акцию
            session.query(UserSubscription).filter_by(
                user_id=user_id, crypto_symbol=crypto_symbol
            ).delete()
            session.commit()
            return UnsubscriptionUserFromCryptoResult.Ok

        finally:
            session.close()

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
