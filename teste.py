import yfinance as yf

data = yf.download("EURUSD=X", period="1d", interval="1m")
print(data.tail())
