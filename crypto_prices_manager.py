import asyncio
from typing import Dict, List

import yfinance as yf
from sqlalchemy import Column, Float, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from coinmarketcap_fetcher import CoinmarketcapPriceFetcher

Base = declarative_base()

API_KEY = "584680a2-ae47-489b-82b7-4c3d35b5f17b"


class CryptoPrice(Base):
    __tablename__ = "crypto_prices"

    id = Column(Integer, primary_key=True)
    symbol = Column(String, unique=True, nullable=False)
    current_price = Column(Float, default=0.00)


class CryptoPricesManager:
    def __init__(self, database_url="sqlite:///crypto_prices.db"):
        self.engine = create_engine(
            database_url, echo=True, connect_args={"check_same_thread": False}
        )
        self.Session = sessionmaker(bind=self.engine)
        self._create_tables()
        self.crypto_fetcher = CoinmarketcapPriceFetcher(
            api_key=API_KEY, num_fetch_coins=200
        )

    def _create_tables(self):
        Base.metadata.create_all(self.engine, checkfirst=True)

    # Можно через метод start_update_all_crypto асинхронно обновляет цены тикеров
    def start_update_all_crypto(self, interval_seconds: int = 60):
        asyncio.create_task(self.update_all_crypto(interval_seconds))

    # Обновляет цены всех акции на таблице crypto_prices
    async def update_all_crypto(self, interval_seconds: int = 60):
        while True:
            try:
                price_by_symbol = self.crypto_fetcher.fetch_top_coins_prices()
                for symbol in price_by_symbol:
                    self.add_crypto_price(symbol, price_by_symbol[symbol])

            except Exception as e:
                print(f"Error updating crypto prices: {e}")

            # Ждет на 60 секунд
            await asyncio.sleep(interval_seconds)

    # Получает все названий тикеров
    def get_all_crypto_symbols(self) -> List[str]:
        session = self.Session()
        try:
            cryptos = session.query(CryptoPrice).all()
            symbols = [str(crypto.symbol) for crypto in cryptos]
            return symbols
        finally:
            session.close()

    # Получает цены всех тикеров
    def get_crypto_prices(self) -> Dict[str, float]:
        session = self.Session()
        try:
            prices = {
                crypto.symbol: crypto.current_price
                for crypto in session.query(CryptoPrice).all()
            }
            return prices
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

    # Проверяет, существует ли тикер в бд
    def crypto_exists(self, symbol: str) -> bool:
        session = self.Session()
        try:
            existing_crypto = (
                session.query(CryptoPrice).filter_by(symbol=symbol).first()
            )
            return existing_crypto is not None
        finally:
            session.close()
