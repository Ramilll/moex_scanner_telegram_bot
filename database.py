import time
import yfinance as yf
from sqlalchemy import create_engine, Column, Float, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()
# Всего 2 таблица- Portfolio с user_id, названиями акции и их ценой когда пользователь подписался на акцию
# и Stocks с названиями акции и текущими ценами
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

# Функция, которая крутится бесконечно и обнавляет цены акции раз в 60 секунд
def update_stock_prices():
    try:
        while True:
            session = Session()
            # обнавляет все текущие цены акции раз в 60 секунд
            for stock in session.query(Stock):
                stock_data = yf.download(stock.symbol, period='1d', interval='1m')
                stock.current_price = stock_data['Close'].iloc[-1]

            session.commit()
            session.close()

            # Спит на 60 секунд перед следующим обновлением
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        pass

# Функция в случае пользователь начал подписаться на акцию
def follow_stock(user_id, stock_symbol):
    session = Session()

    # Добавит акции с текущей акцией в таблицу Stocks, если он не существует
    stock = session.query(Stock).filter_by(symbol=stock_symbol).first()
    if not stock:
        stock_data = yf.download(stock_symbol, period='1d', interval='1m')
        current_price = stock_data['Close'].iloc[-1]

        stock = Stock(symbol=stock_symbol, current_price=current_price)
        session.add(stock)

    # Проверит, существует ли stock_symbol уже в портфолио пользователя
    user_portfolio = session.query(Portfolio).filter_by(user_id=user_id, stock_symbol=stock_symbol).first()

    if user_portfolio:
        # Если акция уже есть в портфеле, обновляет original_price
        stock_data = yf.download(stock_symbol, period='1d', interval='1m')
        user_portfolio.original_price = stock_data['Close'].iloc[-1]
    else:
        # Если пользователь уже следит за акцией, исходная цена(original_price) для этой акции в портфолио пользователя будет обновлена до текущей цены
        stock_data = yf.download(stock_symbol, period='1d', interval='1m')
        original_price = stock_data['Close'].iloc[-1]

        user_portfolio = Portfolio(user_id=user_id, stock_symbol=stock_symbol, original_price=original_price)
        session.add(user_portfolio)

    session.commit()
    session.close()

"""
# Для проверки:
if __name__ == '__main__':
    # Создает SQLite механизм базы данных
    engine = create_engine('sqlite:///stock_bot.db', echo=True)

    # Создает таблиц
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    # Добавить примеры
    follow_stock(1, 'AAPL')
    follow_stock(1, 'TSLA')
    follow_stock(2,'GOOG')
    follow_stock(2,'GOOG')
    follow_stock(2, 'BRK-B')

    update_stock_prices()
"""
