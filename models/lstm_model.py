import numpy as np
import os
import datetime
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential, save_model, load_model
from tensorflow.keras.layers import Dense, LSTM, Dropout

# Function to create a dataset with look-back window
def create_dataset(dataset, look_back=1):
    dataX, dataY = [], []
    for i in range(len(dataset) - look_back):
        dataX.append(dataset[i:(i + look_back), :])
        dataY.append(dataset[i + look_back, 0])  # Only predicting 'Close'
    return np.array(dataX), np.array(dataY)

# Function to inverse transform predictions after scaling
def inverse_transform(arr, scaler, features_count):
    extended = np.zeros((len(arr), features_count))
    extended[:, 0] = arr
    return scaler.inverse_transform(extended)[:, 0]

# Function to build and train the LSTM model
def build_and_train_model(trainX, trainY, look_back, feature_count, epochs=30):
    model = Sequential()
    model.add(LSTM(100, return_sequences=True, input_shape=(look_back, feature_count)))
    model.add(Dropout(0.2))
    model.add(LSTM(50))
    model.add(Dropout(0.2))
    model.add(Dense(1))
    model.compile(loss='mean_squared_error', optimizer='adam')
    
    model.fit(trainX, trainY, epochs=epochs, batch_size=32, verbose=1)
    
    return model

# Function to process the technical data and prepare it for the LSTM model
def process_technical_data(df):
    # Select relevant columns for prediction
    dt_technical = df[['Close', 'MA_50', 'MA_200', 'MACD_line', 'MACD_signal', 'ROC', 'Momentum', 'RSI', 'Upper_Band', 'Lower_Band', 'CCI']]
    dataset_technical = dt_technical[200:]  # Truncate to remove incomplete initial values

    # Scale the dataset using MinMaxScaler
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(dataset_technical)

    # Create dataset with look-back window
    look_back = 5
    dataX, dataY = create_dataset(scaled_data, look_back)

    # Reshape input to [samples, time steps, features]
    dataX = np.reshape(dataX, (dataX.shape[0], look_back, 11))

    # Check if a model for today exists
    current_date = datetime.datetime.now().strftime('%Y%m%d')
    model_filename = f'saved_models/model_{current_date}.h5'
    
    if os.path.exists(model_filename):
        print(f"Model for today ({current_date}) exists. Loading the model...")
        model = load_model(model_filename)
    else:
        print(f"Model for today ({current_date}) not found. Training a new model...")
        # Build and train the LSTM model
        model = build_and_train_model(dataX, dataY, look_back, 11, epochs=30)
        
        # Remove the previous day's model (if it exists)
        delete_previous_model()
        
        # Save the new model
        save_model(model, model_filename)
        print(f"Model saved as {model_filename}")
    
    return model, dataX, dataY, scaler

# Function to delete the previous day's model
def delete_previous_model():
    current_date = datetime.datetime.now()
    previous_day = (current_date - datetime.timedelta(days=1)).strftime('%Y%m%d')
    previous_model_filename = f'saved_models/model_{previous_day}.h5'
    
    if os.path.exists(previous_model_filename):
        os.remove(previous_model_filename)
        print(f"Previous day's model ({previous_model_filename}) deleted.")
    else:
        print(f"No model found for the previous day ({previous_day}).")

# Function to predict future values using the trained model
def predict_future(model, input_data, scaler, feature_count, future_periods=14):
    predictions = []
    current_input = input_data[-1].reshape(1, input_data.shape[1], input_data.shape[2])
    
    for _ in range(future_periods):
        # Predict one step ahead
        next_pred = model.predict(current_input)
        predictions.append(next_pred[0, 0])
        
        # Prepare input for the next prediction
        current_input = np.roll(current_input, -1, axis=1)
        current_input[0, -1, 0] = next_pred[0, 0]
    
    # Inverse scale predictions back to original values
    predictions = inverse_transform(np.array(predictions), scaler, feature_count)
    
    return predictions
