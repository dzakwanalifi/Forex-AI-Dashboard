import * as tf from '@tensorflow/tfjs';

// Function to create a dataset with look-back window
function createDataset(dataset, lookBack = 1) {
    const dataX = [];
    const dataY = [];
    for (let i = 0; i < dataset.length - lookBack; i++) {
        dataX.push(dataset.slice(i, i + lookBack));
        dataY.push(dataset[i + lookBack][0]);  // Only predicting 'Close'
    }
    return [tf.tensor3d(dataX), tf.tensor2d(dataY)];
}

// Function to build and train the LSTM model
async function buildAndTrainModel(trainX, trainY, lookBack, featureCount, epochs = 30) {
    const model = tf.sequential();
    model.add(tf.layers.lstm({units: 100, returnSequences: true, inputShape: [lookBack, featureCount]}));
    model.add(tf.layers.dropout({rate: 0.2}));
    model.add(tf.layers.lstm({units: 50}));
    model.add(tf.layers.dropout({rate: 0.2}));
    model.add(tf.layers.dense({units: 1}));

    model.compile({loss: 'meanSquaredError', optimizer: 'adam'});

    await model.fit(trainX, trainY, {epochs: epochs, batchSize: 32, verbose: 1});

    return model;
}

// Function to process the technical data and prepare it for the LSTM model
async function processTechnicalData(data) {
    const technicalColumns = ['Close', 'MA_50', 'MA_200', 'MACD_line', 'MACD_signal', 'ROC', 'Momentum', 'RSI', 'Upper_Band', 'Lower_Band', 'CCI'];
    const datasetTechnical = data.slice(200);  // Truncate to remove incomplete initial values

    // Normalize the data
    const normalizedData = normalizeData(datasetTechnical, technicalColumns);

    // Create dataset with look-back window
    const lookBack = 5;
    const [dataX, dataY] = createDataset(normalizedData, lookBack);

    // Build and train the LSTM model
    const model = await buildAndTrainModel(dataX, dataY, lookBack, technicalColumns.length, 30);

    return { model, dataX, dataY, normalizedData };
}

// Function to normalize data
function normalizeData(data, columns) {
    const normalized = [];
    for (let col of columns) {
        const values = data.map(row => row[col]);
        const min = Math.min(...values);
        const max = Math.max(...values);
        normalized.push(values.map(v => (v - min) / (max - min)));
    }
    return normalized[0].map((_, i) => normalized.map(col => col[i]));
}

// Function to predict future values using the trained model
async function predictFuture(model, inputData, futurePeriods = 14) {
    let predictions = [];
    let currentInput = inputData.slice(-1);

    for (let i = 0; i < futurePeriods; i++) {
        const prediction = await model.predict(currentInput);
        predictions.push(prediction.dataSync()[0]);

        // Prepare input for the next prediction
        currentInput = tf.concat([currentInput.slice([0, 1]), prediction], 1);
    }

    return predictions;
}

export { processTechnicalData, predictFuture };
