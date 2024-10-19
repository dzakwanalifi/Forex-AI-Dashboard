import pandas as pd
import numpy as np

# Function to calculate Moving Average (MA)
def moving_average(data, period):
    return data['Close'].rolling(window=period).mean()

# Function to calculate MACD and Signal Line
def macd(data, short_period=12, long_period=26, signal_period=9):
    short_ema = data['Close'].ewm(span=short_period, adjust=False).mean()
    long_ema = data['Close'].ewm(span=long_period, adjust=False).mean()
    macd_line = short_ema - long_ema
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    return macd_line, signal_line

# Function to calculate Rate of Change (ROC)
def rate_of_change(data, period=2):
    return data['Close'].pct_change(periods=period)

# Function to calculate Momentum
def momentum(data, period=4):
    return data['Close'].diff(period)

# Function to calculate Relative Strength Index (RSI)
def rsi(data, period=10):
    delta = data['Close'].diff(1)
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rs = rs.replace([np.inf, -np.inf], np.nan)
    return 100 - (100 / (1 + rs))

# Function to calculate Bollinger Bands
def bollinger_bands(data, period=20, num_std=2):
    sma = data['Close'].rolling(window=period).mean()
    rolling_std = data['Close'].rolling(window=period).std()
    upper_band = sma + (rolling_std * num_std)
    lower_band = sma - (rolling_std * num_std)
    return upper_band, lower_band

# Function to calculate Commodity Channel Index (CCI)
def cci(data, ndays=20):
    tp = (data['High'] + data['Low'] + data['Close']) / 3 if 'High' in data.columns and 'Low' in data.columns else data['Close']
    sma = tp.rolling(ndays).mean()
    mad = tp.rolling(ndays).apply(lambda x: np.abs(x - x.mean()).mean())
    cci = (tp - sma) / (0.015 * mad)
    return cci

# Function to apply all technical indicators to the dataset
def apply_technical_indicators(data):
    # Applying various technical indicators to the dataset
    data['MA_50'] = moving_average(data, 50)
    data['MA_200'] = moving_average(data, 200)
    data['MACD_line'], data['MACD_signal'] = macd(data)
    data['ROC'] = rate_of_change(data)
    data['Momentum'] = momentum(data)
    data['RSI'] = rsi(data)
    data['Upper_Band'], data['Lower_Band'] = bollinger_bands(data)
    data['CCI'] = cci(data)

    # Handle missing values with forward and backward fill
    indicators = ['MA_50', 'MA_200', 'MACD_line', 'MACD_signal', 'ROC', 'Momentum', 'RSI', 'Upper_Band', 'Lower_Band', 'CCI']
    for col in indicators:
        data[col] = data[col].ffill().bfill()

    return data
