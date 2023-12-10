import asyncio
import time
import yfinance as yf
from sqlalchemy import create_engine, Column, Float, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()


class Portfolio(Base):
    __tablename__ = 'portfolio'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    stock_symbol = Column(String, nullable=False)
    original_price = Column(Float, nullable=False)


class Stock(Base):
    __tablename__ = 'stocks'

    id = Column(Integer, primary_key=True)
    symbol = Column(String, unique=True, nullable=False)
    current_price = Column(Float, default=0.0)


class StockBot:
    def __init__(self, database_url='sqlite:///stock_bot.db'):
        self.engine = create_engine(database_url, echo=True)
        self.Session = sessionmaker(bind=self.engine)
        self.create_tables()

    def create_tables(self):
        Base.metadata.create_all(self.engine)

    async def update_stock_prices(self):
        try:
            while True:
                await self.update_stocks()
                await asyncio.sleep(60)
        except asyncio.CancelledError:
            pass

    async def update_stocks(self):
        session = self.Session()
        for stock in session.query(Stock):
            stock_data = yf.download(stock.symbol, period='1d', interval='1m')
            stock.current_price = stock_data['Close'].iloc[-1]

        session.commit()
        session.close()

    async def follow_stock(self, user_id, stock_symbol):
        session = self.Session()

        stock = session.query(Stock).filter_by(symbol=stock_symbol).first()
        if not stock:
            stock_data = yf.download(stock_symbol, period='1d', interval='1m')
            current_price = stock_data['Close'].iloc[-1]
            stock = Stock(symbol=stock_symbol, current_price=current_price)
            session.add(stock)

        user_portfolio = session.query(Portfolio).filter_by(user_id=user_id, stock_symbol=stock_symbol).first()

        if user_portfolio:
            stock_data = yf.download(stock_symbol, period='1d', interval='1m')
            user_portfolio.original_price = stock_data['Close'].iloc[-1]
        else:
            stock_data = yf.download(stock_symbol, period='1d', interval='1m')
            original_price = stock_data['Close'].iloc[-1]
            user_portfolio = Portfolio(user_id=user_id, stock_symbol=stock_symbol, original_price=original_price)
            session.add(user_portfolio)

        session.commit()
        session.close()

"""
if __name__ == '__main__':
    bot = StockBot()

    async def main():
        await asyncio.gather(
            bot.update_stock_prices(),
            bot.follow_stock(1, 'AAPL'), 
            bot.follow_stock(1, 'TSLA'),
            bot.follow_stock(2, 'GOOG'),
            bot.follow_stock(2, 'GOOG'),
            bot.follow_stock(2, 'BRK-B')
        )

    asyncio.run(main())
"""
