from typing import Dict, List
from enum import Enum

import yfinance as yf
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from stocks_prices_manager import StocksPricesManager

Base = declarative_base()


class SubscriptionUserToStockResult(Enum):
    Ok = 1
    NoSuchStock = 2
    AlreadySubscribed = 3


class UnsubscriptionUserToStockResult(Enum):
    Ok = 1
    NotSubscribed = 2


class UserSubscription(Base):
    # Определение таблицы для подписок пользователей
    __tablename__ = "user_subscriptions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    stock_symbol = Column(String, nullable=False)


class SubscriptionsManager:
    def __init__(self, database_url="sqlite:///subscription_data.db"):
        # Инициализация менеджера подписок с указанием базы данных
        self.engine = create_engine(
            database_url, echo=True, connect_args={"check_same_thread": False}
        )
        self.Session = sessionmaker(bind=self.engine)
        self.create_tables()

    def create_tables(self) -> None:
        # Создание необходимых таблиц в базе данных
        Base.metadata.create_all(self.engine, checkfirst=True)
        stock_manager = StocksPricesManager()
        stock_manager.create_tables()

    async def subscribe_user_to_stock(
        self, user_id: int, stock_symbol: str
    ) -> SubscriptionUserToStockResult:
        session = self.Session()
        try:
            stock_manager = StocksPricesManager()

            if not stock_manager.stock_exists(stock_symbol):
                return SubscriptionUserToStockResult.NoSuchStock

            existing_subscription = (
                session.query(UserSubscription)
                .filter_by(user_id=user_id, stock_symbol=stock_symbol)
                .first()
            )
            if existing_subscription:
                return SubscriptionUserToStockResult.AlreadySubscribed

            # Подписываем пользователя
            subscription = UserSubscription(user_id=user_id, stock_symbol=stock_symbol)
            session.merge(subscription)
            session.commit()
            return SubscriptionUserToStockResult.Ok

        finally:
            session.close()
            return SubscriptionUserToStockResult.Ok

    # Отмена подписки пользователя на акцию
    def unsubscribe_user_from_stock(
        self, user_id: int, stock_symbol: str
    ) -> UnsubscriptionUserToStockResult:
        session = self.Session()
        try:
            subscription = (
                session.query(UserSubscription)
                .filter_by(user_id=user_id, stock_symbol=stock_symbol)
                .first()
            )
            if not subscription:
                return UnsubscriptionUserToStockResult.NotSubscribed
            # Отмена подписки пользователя на акцию
            session.query(UserSubscription).filter_by(
                user_id=user_id, stock_symbol=stock_symbol
            ).delete()
            session.commit()
            return UnsubscriptionUserToStockResult.Ok

        finally:
            session.close()
            return UnsubscriptionUserToStockResult.Ok

    # Получение списка акций, на которые подписан пользователь
    def get_user_subscriptions(self, user_id: int) -> List[str]:
        session = self.Session()
        try:
            subscriptions = [
                sub.stock_symbol
                for sub in session.query(UserSubscription)
                .filter_by(user_id=user_id)
                .all()
            ]
            return [str(symbol) for symbol in subscriptions]
        finally:
            session.close()

    # Получить подписку всех пользователей на какую-то акцию
    def get_all_subscribed_users_to_stock(self, stock_symbol: str) -> List[int]:
        session = self.Session()
        try:
            # Для извлечения ид пользователей
            users = [
                sub.user_id
                for sub in session.query(UserSubscription.user_id)
                .filter_by(stock_symbol=stock_symbol)
                .all()
            ]
            return users
        finally:
            session.close()
