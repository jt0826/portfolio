import yfinance as yf
from exchange_rate import ExchangeRate


class InvalidTickerException(Exception):
    """Exception raised for invalid ticker symbols."""
    pass


class PullData:
    def __init__(self, ticker_symbol):
        try:
            # Get the data of the stock
            stock = yf.Ticker(ticker_symbol)

            # Check if the ticker is valid by attempting to access its info
            if not stock.history:
                raise InvalidTickerException(f"Invalid ticker symbol: {ticker_symbol}")

            # Get the historical prices for the stock
            historical_prices = stock.history(period='1d', interval='1m')

            # Get the latest price and time
            self.latest_price = historical_prices['Close'].iloc[-1]
            self.latest_time = historical_prices.index[-1].strftime('%H:%M:%S')
            self.ticker_symbol = ticker_symbol
            self.historical_prices = historical_prices
            self.currency = stock.info['currency']
            self.foreignto_sgd = ExchangeRate(self.currency).foreignto_sgd
        except Exception as e:
            raise InvalidTickerException(f"Error retrieving data for ticker symbol {ticker_symbol}: {str(e)}")
