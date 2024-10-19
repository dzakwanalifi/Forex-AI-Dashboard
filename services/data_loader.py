import pandas as pd
import yfinance as yf
import numpy as np

# Dictionary to map Indonesian month names to numbers
indonesian_months = {
    'Januari': '01', 'Februari': '02', 'Maret': '03', 'April': '04',
    'Mei': '05', 'Juni': '06', 'Juli': '07', 'Agustus': '08',
    'September': '09', 'Oktober': '10', 'November': '11', 'Desember': '12'
}

# Custom date parser for Indonesian date format (e.g., Januari 2023)
def parse_indonesian_date(date_string):
    if len(date_string.split()) == 2:
        month, year = date_string.split()
    else:
        month = date_string
        year = str(pd.Timestamp.now().year)
    month_num = indonesian_months[month]
    return pd.to_datetime(f'{year}-{month_num}-01')

def calculate_trend(current_value, previous_value):
    if current_value is None or previous_value is None:
        return 'neutral'
    if current_value > previous_value:
        return 'up'
    elif current_value < previous_value:
        return 'down'
    else:
        return 'neutral'

# Function to load US inflation data
def load_inflation_data_us():
    try:
        inflation_us = pd.read_csv('data/inflation_rate.csv', index_col=0)
        inflation_us['Periode'] = inflation_us['Year'].astype(str) + '-' + inflation_us['Month'].astype(str)
        inflation_us = inflation_us.drop(columns=['Year', 'Month'])
        inflation_us['Periode'] = pd.to_datetime(inflation_us['Periode'])
        inflation_us = inflation_us.sort_values('Periode')
        current_rate = inflation_us.iloc[-1]['Inflation Rate']
        previous_rate = inflation_us.iloc[-2]['Inflation Rate'] if len(inflation_us) > 1 else None
        trend = calculate_trend(current_rate, previous_rate)
        return float(current_rate) if not np.isnan(current_rate) else None, trend
    except Exception as e:
        print(f"Error loading US inflation data: {e}")
        return None, 'neutral'

# Function to load Indonesia inflation data
def load_inflation_data_id():
    try:
        inflation_id = pd.read_excel('data/Data Inflasi.xlsx', index_col=0)
        inflation_id['Periode'] = inflation_id['Periode'].apply(parse_indonesian_date)
        inflation_id = inflation_id.sort_values('Periode')
        current_rate = inflation_id.iloc[-1]['Data Inflasi']
        previous_rate = inflation_id.iloc[-2]['Data Inflasi'] if len(inflation_id) > 1 else None
        current_rate = float(current_rate.strip('%'))
        previous_rate = float(previous_rate.strip('%')) if previous_rate else None
        trend = calculate_trend(current_rate, previous_rate)
        return current_rate if not np.isnan(current_rate) else None, trend
    except Exception as e:
        print(f"Error loading Indonesia inflation data: {e}")
        return None, 'neutral'

# Function to load BI Rate
def load_bi_rate():
    try:
        bi_rate = pd.read_excel('data/BI-Rate.xlsx', index_col=0)
        bi_rate['Tanggal'] = bi_rate['Tanggal'].str.split().str[1:]
        bi_rate['Tanggal'] = bi_rate['Tanggal'].apply(lambda x: ' '.join(x) if len(x) > 1 else x[0])
        bi_rate['Tanggal'] = bi_rate['Tanggal'].apply(parse_indonesian_date)
        bi_rate = bi_rate.sort_values('Tanggal')
        current_rate = bi_rate.iloc[-1]['BI-7Day-RR']
        previous_rate = bi_rate.iloc[-2]['BI-7Day-RR'] if len(bi_rate) > 1 else None
        current_rate = float(current_rate.strip('%'))
        previous_rate = float(previous_rate.strip('%')) if previous_rate else None
        trend = calculate_trend(current_rate, previous_rate)
        return current_rate if not np.isnan(current_rate) else None, trend
    except Exception as e:
        print(f"Error loading BI rate: {e}")
        return None, 'neutral'

# Function to load Fed Rate data
def load_fed_rate():
    try:
        fed_rate = pd.read_csv('data/Feds Funds Rate.csv')
        fed_rate['DATE'] = pd.to_datetime(fed_rate['DATE'])
        fed_rate = fed_rate.sort_values('DATE')
        current_rate = fed_rate.iloc[-1]['DFF']
        previous_rate = fed_rate.iloc[-2]['DFF'] if len(fed_rate) > 1 else None
        trend = calculate_trend(current_rate, previous_rate)
        return float(current_rate) if not np.isnan(current_rate) else None, trend
    except Exception as e:
        print(f"Error loading Fed rate: {e}")
        return None, 'neutral'

# Function to load JKSE stock index data
def load_jkse():
    try:
        jkse_ticker = yf.Ticker('^JKSE')
        jkse = jkse_ticker.history(interval='1d')
        if jkse.empty:
            print("No data available for JKSE")
            return None, 'neutral'
        current_price = jkse['Close'].iloc[-1]
        previous_price = jkse['Close'].iloc[-2] if len(jkse) > 1 else None
        trend = calculate_trend(current_price, previous_price)
        return float(current_price), trend
    except Exception as e:
        print(f"Error loading JKSE data: {e}")
        return None, 'neutral'

# Function to load S&P 500 stock index data
def load_sp500():
    try:
        sp500_ticker = yf.Ticker('^GSPC')
        sp500 = sp500_ticker.history(interval='1d')
        if sp500.empty:
            print("No data available for S&P 500")
            return None, 'neutral'
        current_price = sp500['Close'].iloc[-1]
        previous_price = sp500['Close'].iloc[-2] if len(sp500) > 1 else None
        trend = calculate_trend(current_price, previous_price)
        return float(current_price), trend
    except Exception as e:
        print(f"Error loading S&P 500 data: {e}")
        return None, 'neutral'

def handle_nan(obj):
    if isinstance(obj, (pd.DataFrame, pd.Series)):
        return obj.where(pd.notnull(obj), None)
    elif isinstance(obj, (float, np.float64)) and np.isnan(obj):
        return None
    return obj

# Function to load USD/IDR exchange rate data
def load_usdidr():
    try:
        # Load data USDIDR dari Yahoo Finance
        usdidr_ticker = yf.Ticker('USDIDR=X')
        usdidr = usdidr_ticker.history(period='max', interval='1d')
        
        if usdidr.empty:
            print("No data available for USD/IDR")
            return None, 'neutral', pd.DataFrame(), pd.DataFrame()
        
        # Konversi ke timezone Asia/Jakarta
        usdidr.index = usdidr.index.tz_convert('Asia/Jakarta')
        
        # Drop kolom yang tidak diperlukan
        usdidr = usdidr.drop(columns=['Volume', 'Dividends', 'Stock Splits'])
        
        # Ambil hanya tanggal dari index
        usdidr.index = usdidr.index.date
        
        # Rename kolom Close untuk lebih jelas, tapi tetap pertahankan nama 'Close' untuk kompatibilitas
        usdidr = usdidr.rename(columns={'Close': 'Close_idr'})
        usdidr['Close'] = usdidr['Close_idr']  # Duplikasi kolom untuk kompatibilitas
        
        # pastikan semua tanggal ada dan tidak ada yang terlewat, jika ada yang terlewat atau NA atau 0 maka interpolasi waktu
        usdidr = usdidr.asfreq('B')
        
        # Identifikasi nilai yang kurang dari 6000 dan set sebagai NaN
        usdidr.loc[usdidr['Close_idr'] < 6000, 'Close_idr'] = np.nan
        usdidr.loc[usdidr['Close'] < 6000, 'Close'] = np.nan
        
        # fill NA atau 0 dengan interpolasi waktu
        usdidr = usdidr.interpolate(method='time')
        
        # buat current usdidr yang berisi usd idr pada periode terakhir
        current_usdidr = usdidr.sort_index().iloc[-1]['Close_idr']
        
        # ambil data 30 hari ke belakang dari data terbaru sort
        usdidr_30days = usdidr.sort_index().iloc[-30:]
        
        # Hitung trend
        previous_usdidr = usdidr.sort_index().iloc[-2]['Close_idr'] if len(usdidr) > 1 else None
        trend = calculate_trend(current_usdidr, previous_usdidr)
        
        # Reset index dan rename index column to 'Date'
        usdidr = usdidr.reset_index().rename(columns={'index': 'Date'})
        usdidr_30days = usdidr_30days.reset_index().rename(columns={'index': 'Date'})
        
        # Convert Date to string format
        usdidr['Date'] = usdidr['Date'].astype(str)
        usdidr_30days['Date'] = usdidr_30days['Date'].astype(str)
        
        return current_usdidr, trend, usdidr_30days, usdidr
    except Exception as e:
        print(f"Error loading USD/IDR data: {e}")
        return None, 'neutral', pd.DataFrame(columns=['Date', 'Close', 'Close_idr']), pd.DataFrame(columns=['Date', 'Close', 'Close_idr'])
