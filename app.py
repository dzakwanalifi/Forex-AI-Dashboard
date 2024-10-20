from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from services.data_loader import load_inflation_data_us, load_inflation_data_id, load_bi_rate, load_fed_rate, load_jkse, load_sp500, load_usdidr
from models.technical_indicators import apply_technical_indicators
from services.news_service import get_combined_news 
from services.gemini_service import generate_recommendation, generate_analysis_report_and_recommendation
import math
from datetime import datetime, timedelta
import numpy as np
import json
from datetime import date
import pandas as pd
from flask_assets import Environment, Bundle
import logging
import os

app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app)

logging.getLogger('webassets').addHandler(logging.StreamHandler())
logging.getLogger('webassets').setLevel(logging.DEBUG)

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if pd.isna(obj):
            return None
        return super(NpEncoder, self).default(obj)

# Global variables
global_predictions = None
last_prediction_time = None
prediction_cache_duration = timedelta(hours=1)  # Cache duration, adjust as needed

def safe_float(value):
    if isinstance(value, dict):
        # Jika nilai adalah dictionary, coba ambil nilai 'predicted_usdidr'
        value = value.get('predicted_usdidr', None)
    
    if value is None:
        return None
    try:
        float_value = float(value)
        return float_value if not math.isnan(float_value) else None
    except (ValueError, TypeError):
        return None

def get_or_update_predictions(forecast_days=14):
    global global_predictions, last_prediction_time
    
    current_time = datetime.now()
    if global_predictions is None or last_prediction_time is None or (current_time - last_prediction_time) > prediction_cache_duration:
        # Load data
        _, _, _, usdidr_full = load_usdidr()
        if usdidr_full.empty:
            app.logger.warning("USD/IDR data is empty. Unable to make predictions.")
            return []
        
        usdidr_with_indicators = apply_technical_indicators(usdidr_full)
        if usdidr_with_indicators.empty:
            app.logger.warning("Technical indicators data is empty. Unable to make predictions.")
            return []
        
        # Kirim data ke frontend untuk diproses
        global_predictions = usdidr_with_indicators.to_dict('records')
        last_prediction_time = current_time
    
    # Pastikan kita hanya mengembalikan nilai prediksi, bukan seluruh dictionary
    return [safe_float(pred.get('Close', pred.get('predicted_usdidr', None))) for pred in global_predictions[-forecast_days:]]

@app.route('/')
def index():
    return render_template('index.html') 

@app.route('/api/data', methods=['GET'])
def get_economic_indicators():
    try:
        app.logger.info("Fetching economic indicators")
        
        forecast_days = int(request.args.get('forecast_days', 14))
        
        # Load all necessary economic indicators
        inflation_us, inflation_us_trend = load_inflation_data_us()
        inflation_id, inflation_id_trend = load_inflation_data_id()
        bi_rate, bi_rate_trend = load_bi_rate()
        fed_rate, fed_rate_trend = load_fed_rate()
        jkse, jkse_trend = load_jkse()
        sp500, sp500_trend = load_sp500()
        current_usdidr, usdidr_trend, usdidr_30days, usdidr_full = load_usdidr()

        app.logger.info(f"Loaded economic indicators: {inflation_us}, {inflation_id}, {bi_rate}, {fed_rate}, {jkse}, {sp500}, {current_usdidr}")

        # Apply technical indicators to the full USD/IDR dataset
        if not usdidr_full.empty and 'Close' in usdidr_full.columns:
            usdidr_with_indicators = apply_technical_indicators(usdidr_full)
        else:
            usdidr_with_indicators = pd.DataFrame()

        # Get or update predictions
        predictions = get_or_update_predictions(forecast_days)

        # Prepare USDIDR history
        usdidr_history = usdidr_full[['Date', 'Close']].to_dict('records') if not usdidr_full.empty else []

        app.logger.info(f"USDIDR history: {usdidr_history}")

        # Prepare predictions for the specified number of days
        prediction_data = [{'day': i+1, 'predicted_usdidr': safe_float(pred)} for i, pred in enumerate(predictions)] if predictions is not None and len(predictions) > 0 else []

        app.logger.info(f"USDIDR predictions: {prediction_data}")

        # Fetch latest news
        news_df = get_combined_news()
        news_text = news_df['Title'].to_markdown(index=False) if not news_df.empty else "No recent news available."

        # Generate AI Insight
        ai_insight = generate_analysis_report_and_recommendation(
            fed_rate=safe_float(fed_rate),
            bi_rate=safe_float(bi_rate),
            inflation_id=safe_float(inflation_id),
            inflation_us=safe_float(inflation_us),
            current_jkse=safe_float(jkse),
            current_sp500=safe_float(sp500),
            current_usdidr=safe_float(current_usdidr),
            usdidr_1month_ago=safe_float(usdidr_30days.iloc[0]['Close']) if usdidr_30days is not None and len(usdidr_30days) > 0 else None,
            predictions=[safe_float(p['predicted_usdidr']) for p in prediction_data],
            news_text=news_text
        )

        json_response = {
            'inflation_us': safe_float(inflation_us),
            'inflation_us_trend': inflation_us_trend,
            'inflation_id': safe_float(inflation_id),
            'inflation_id_trend': inflation_id_trend,
            'bi_rate': safe_float(bi_rate),
            'bi_rate_trend': bi_rate_trend,
            'fed_rate': safe_float(fed_rate),
            'fed_rate_trend': fed_rate_trend,
            'jkse': safe_float(jkse),
            'jkse_trend': jkse_trend,
            'sp500': safe_float(sp500),
            'sp500_trend': sp500_trend,
            'current_usdidr': safe_float(current_usdidr),
            'usdidr_trend': usdidr_trend,
            'usdidr_history': usdidr_history,
            'usdidr_data': [{k: safe_float(v) if isinstance(v, (int, float)) else v for k, v in d.items()} for d in usdidr_with_indicators.to_dict('records')] if not usdidr_with_indicators.empty else [],
            'usdidr_predictions': prediction_data,
            'ai_insight': ai_insight
        }

        app.logger.info(f"Sending data to frontend: {json_response}")
        return jsonify(json_response)
    except Exception as e:
        app.logger.error(f"Error in get_economic_indicators: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/news', methods=['GET'])
def get_news():
    try:
        app.logger.info("Fetching news")
        # Fetch combined news from all routes
        news_df = get_combined_news()
        
        # Ensure all necessary columns are present and rename them if needed
        column_mapping = {
            'Title': 'headline',
            'Description': 'summary',
            'Source': 'source',
            'Publication Date': 'date',
            'Link': 'link',
            'Image': 'image'  # Add this line
        }
        news_df = news_df.rename(columns=column_mapping)
        
        required_columns = ['headline', 'summary', 'source', 'date', 'link', 'image']  # Add 'image' here
        for col in required_columns:
            if col not in news_df.columns:
                news_df[col] = 'N/A'
        
        # Convert date to string format if it's not already
        news_df['date'] = news_df['date'].astype(str)
        
        # Convert news DataFrame to list of dictionaries
        news_list = news_df[required_columns].to_dict(orient='records')
        
        # Return the news data in JSON format
        app.logger.info(f"Returning news: {news_list}")
        return jsonify({'news': news_list})
    except Exception as e:
        app.logger.error(f"Error in get_news: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

session_history = {}

@app.route('/api/ai-recommendation', methods=['POST'])
def get_ai_recommendation():
    try:
        app.logger.info("Received AI recommendation request")
        
        # Load economic indicators and predictions
        inflation_us, _ = load_inflation_data_us()
        inflation_id, _ = load_inflation_data_id()
        bi_rate, _ = load_bi_rate()
        fed_rate, _ = load_fed_rate()
        jkse, _ = load_jkse()
        sp500, _ = load_sp500()
        current_usdidr, _, usdidr_30days, _ = load_usdidr()

        # Get predictions
        predictions = get_or_update_predictions()

        # Fetch latest news
        news_df = get_combined_news()
        news_text = news_df['Title'].to_markdown(index=False)

        # Get user question and session ID from the request body
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        user_question = data.get('question', 'Apa rekomendasi Anda?')
        session_id = data.get('session_id')

        if not session_id:
            return jsonify({'error': 'Session ID is required.'}), 400

        app.logger.info(f"Processing request for session {session_id}")

        # Check if session history exists, otherwise initialize it with welcome message
        if session_id not in session_history:
            welcome_message = {
                "role": "assistant",
                "content": "Selamat datang di AI Trading Assistant! Saya siap membantu Anda dengan analisis dan rekomendasi trading forex USD/IDR. Silakan ajukan pertanyaan atau minta saran tentang kondisi pasar saat ini."
            }
            session_history[session_id] = [welcome_message]

        # Generate AI-based recommendation
        updated_history = generate_recommendation(
            fed_rate=safe_float(fed_rate),
            bi_rate=safe_float(bi_rate),
            inflation_id=safe_float(inflation_id),
            inflation_us=safe_float(inflation_us),
            current_jkse=safe_float(jkse),
            current_sp500=safe_float(sp500),
            current_usdidr=safe_float(current_usdidr),
            usdidr_1month_ago=safe_float(usdidr_30days.iloc[0]['Close']) if usdidr_30days is not None and len(usdidr_30days) > 0 else None,
            predictions=[safe_float(p) for p in predictions] if predictions is not None else [],
            news_text=news_text,
            user_question=user_question,
            history=session_history[session_id]
        )

        # Update session history with the new conversation
        session_history[session_id] = updated_history

        app.logger.info(f"AI recommendation generated successfully for session {session_id}")

        # Return the AI recommendation and updated chat history
        return jsonify({
            'chat_history': updated_history
        })
    except Exception as e:
        app.logger.error(f"Error in get_ai_recommendation: {str(e)}", exc_info=True)
        error_message = "Terjadi kesalahan saat memproses permintaan Anda. Silakan coba lagi nanti."
        return jsonify({
            'error': error_message,
            'details': str(e)
        }), 500

# Konfigurasi Flask-Assets
assets = Environment(app)
css = Bundle('css/styles.css', output='gen/styles.css')
assets.register('css_all', css)

js = Bundle('js/dashboard.js', output='gen/bundle.js')
assets.register('js_all', js)

@app.route('/all-news')
def all_news():
    return render_template('all_news.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
