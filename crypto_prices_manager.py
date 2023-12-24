from typing import Dict, Set

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
        self.cnt_update_all_crypto_calls = 0
        self._last_cnt_update_all_crypto_calls = None

    # Обновляет цены всех акции на таблице crypto_prices
    def update_all_crypto(self):
        try:
            price_by_symbol = self.crypto_fetcher.fetch_top_coins_prices()
            for symbol in price_by_symbol:
                self._add_crypto_price(symbol, price_by_symbol[symbol])
            self.cnt_update_all_crypto_calls += 1

        except Exception as e:
            print(f"Error updating crypto prices: {e}")

    # Получает все названий тикеров
    def get_all_crypto_symbols(self) -> Set[str]:
        return self.get_crypto_prices().keys()

    # Проверяет, существует ли тикер в бд
    def crypto_exists(self, symbol: str) -> bool:
        return symbol in self.get_all_crypto_symbols()

    # Получает цены всех тикеров
    def get_crypto_prices(self) -> Dict[str, float]:
        # if nothing is updated, return the last price_by_symbol
        if self._last_cnt_update_all_crypto_calls == self.cnt_update_all_crypto_calls:
            return self._last_price_by_symbol

        session = self.Session()
        try:
            price_by_symbol = {
                crypto.symbol: crypto.current_price
                for crypto in session.query(CryptoPrice).all()
            }
            self._last_price_by_symbol = price_by_symbol
            self._last_cnt_update_all_crypto_calls = self.cnt_update_all_crypto_calls
            return price_by_symbol
        finally:
            session.close()

    def _create_tables(self):
        Base.metadata.create_all(self.engine, checkfirst=True)

    # Добавляет цену тикера
    def _add_crypto_price(self, symbol: str, current_price: float):
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
