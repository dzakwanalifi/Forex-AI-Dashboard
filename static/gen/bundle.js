import { processTechnicalData, predictFuture } from './lstm_model.js';

const API_BASE_URL = '/api';
let chart; // Global variable to store the chart instance
let sessionId; // Global variable to store the session ID
let globalEconomicData; // Global variable to store economic data
let globalHistoricalData;
let globalPredictions;
let lstmModel;

// Function to generate a new session ID
function generateSessionId() {
    return Date.now().toString();
}

// Function to update the chart
function updateChart(historicalData, predictions, forecastDays, historicalDays) {
    const ctx = document.getElementById('usd-idr-chart').getContext('2d');
    
    if (!historicalData || historicalData.length === 0 || !predictions || predictions.length === 0) {
        console.log("No data available for chart");
        ctx.font = '20px Arial';
        ctx.fillStyle = 'gray';
        ctx.textAlign = 'center';
        ctx.fillText('No data available', ctx.canvas.width / 2, ctx.canvas.height / 2);
        return;
    }

    console.log("Historical Data:", historicalData);
    console.log("Predictions:", predictions);

    const filteredHistoricalData = historicalData.slice(-historicalDays);
    const filteredPredictions = predictions.slice(0, forecastDays);

    const historicalDates = filteredHistoricalData.map(d => new Date(d.Date));
    const futureDates = filteredPredictions.map((_, index) => {
        const lastDate = new Date(filteredHistoricalData[filteredHistoricalData.length - 1].Date);
        return new Date(lastDate.setDate(lastDate.getDate() + index + 1));
    });
    
    const labels = [...historicalDates, ...futureDates];
    const historicalValues = filteredHistoricalData.map(d => d.Close);
    const predictionValues = filteredPredictions.map(d => d.predicted_usdidr);

    // Menambahkan titik terakhir dari data historis ke awal prediksi
    const lastHistoricalValue = historicalValues[historicalValues.length - 1];
    const combinedPredictionValues = [lastHistoricalValue, ...predictionValues];

    console.log("Chart Data:", { labels, historicalValues, combinedPredictionValues });

    if (chart) {
        chart.destroy();
    }

    chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Historical USD/IDR',
                data: historicalValues,
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1,
                pointRadius: 2,
            }, {
                label: 'Predicted USD/IDR',
                data: [...Array(historicalValues.length - 1).fill(null), ...combinedPredictionValues],
                borderColor: 'rgb(255, 99, 132)',
                borderDash: [5, 5],
                tension: 0.1,
                pointRadius: 2,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'day',
                        displayFormats: {
                            day: 'MMM d'
                        }
                    },
                    title: {
                        display: true,
                        text: 'Date'
                    },
                    ticks: {
                        maxTicksLimit: 10
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'USD/IDR Exchange Rate'
                    },
                    suggestedMin: Math.min(...historicalValues, ...combinedPredictionValues) * 0.99,
                    suggestedMax: Math.max(...historicalValues, ...combinedPredictionValues) * 1.01
                }
            },
            plugins: {
                tooltip: {
                    mode: 'index',
                    intersect: false
                },
                legend: {
                    position: 'top',
                }
            }
        }
    });
}

// Function to show loading popup
function showLoadingPopup() {
    document.getElementById('loading-popup').style.display = 'flex';
}

// Function to hide loading popup
function hideLoadingPopup() {
    document.getElementById('loading-popup').style.display = 'none';
}

// Function to fetch all data
async function fetchAllData() {
    showLoadingPopup();
    try {
        const [economicData, newsData] = await Promise.all([
            fetchEconomicIndicators(),
            fetchNews()
        ]);
        globalEconomicData = economicData; // Store economic data globally
        hideLoadingPopup();
        return { economicData, newsData };
    } catch (error) {
        console.error('Error fetching data:', error);
        hideLoadingPopup();
        throw error;
    }
}

async function initializeLSTM(data) {
    try {
        const { model, dataX } = await processTechnicalData(data.usdidr_data);
        lstmModel = model;
        globalPredictions = await predictFuture(model, dataX, 14);
        console.log("LSTM model initialized and predictions made:", globalPredictions);
        updateChart(data.usdidr_history, globalPredictions, 14, 30);
    } catch (error) {
        console.error("Error initializing LSTM model:", error);
    }
}

// Fetch economic indicators and update the UI
async function fetchEconomicIndicators(forecastDays = 14) {
    console.log("Fetching economic indicators");
    try {
        const response = await fetch(`${API_BASE_URL}/data?forecast_days=${forecastDays}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        console.log("Economic data received:", data);

        globalEconomicData = data;
        globalHistoricalData = data.usdidr_history;
        globalPredictions = data.usdidr_predictions;

        updateEconomicIndicators(data);
        updateChart(data.usdidr_history, data.usdidr_predictions, forecastDays, 30);
        updateAIInsight(data);
        return data;
    } catch (error) {
        console.error('Error fetching economic indicators:', error);
        document.getElementById('economic-indicators').innerHTML = `<p class="text-red-500">Error loading economic indicators: ${error.message}. Please try again later.</p>`;
        throw error;
    }
}

function updateAIInsight(data) {
    const aiInsightContent = document.getElementById('ai-insight-content');
    const rawContent = data.ai_insight;

    let parsedContent = rawContent;

    // Check if marked is available and use it to parse Markdown
    if (typeof marked !== 'undefined') {
        parsedContent = marked.parse(rawContent);
    }

    aiInsightContent.innerHTML = `<div class="markdown-content">${parsedContent}</div>`;
}

// Fetch latest news and update the UI
async function fetchNews() {
    console.log("Fetching news");
    try {
        const response = await fetch(`${API_BASE_URL}/news`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        console.log("News data received:", data);
        updateNews(data);
        return data;
    } catch (error) {
        console.error('Error fetching news:', error);
        const newsContainer = document.getElementById('news-items');
        newsContainer.innerHTML = `<p class="text-red-500">Error loading news: ${error.message}. Please try again later.</p>`;
        throw error;
    }
}

// Update economic indicators
function updateEconomicIndicators(data) {
    const indicatorsContainer = document.getElementById('economic-indicators');
    indicatorsContainer.innerHTML = ''; // Clear existing content

    const indicators = [
        { title: 'USD/IDR', value: data.current_usdidr != null ? data.current_usdidr.toFixed(2) : 'N/A', trend: data.usdidr_trend, icon: 'fa-dollar-sign' },
        { title: 'Inflation US', value: data.inflation_us != null ? data.inflation_us.toFixed(2) + '%' : 'N/A', trend: data.inflation_us_trend, icon: 'fa-percentage' },
        { title: 'Inflation ID', value: data.inflation_id != null ? data.inflation_id.toFixed(2) + '%' : 'N/A', trend: data.inflation_id_trend, icon: 'fa-percentage' },
        { title: 'BI Rate', value: data.bi_rate != null ? data.bi_rate.toFixed(2) + '%' : 'N/A', trend: data.bi_rate_trend, icon: 'fa-chart-line' },
        { title: 'Fed Rate', value: data.fed_rate != null ? data.fed_rate.toFixed(2) + '%' : 'N/A', trend: data.fed_rate_trend, icon: 'fa-university' },
        { title: 'JKSE', value: data.jkse != null ? data.jkse.toFixed(2) : 'N/A', trend: data.jkse_trend, icon: 'fa-chart-bar' },
        { title: 'S&P 500', value: data.sp500 != null ? data.sp500.toFixed(2) : 'N/A', trend: data.sp500_trend, icon: 'fa-chart-line' }
    ];

    indicators.forEach(indicator => {
        const indicatorHtml = `
            <div class="bg-white p-4 rounded-lg shadow-md hover:shadow-lg transition-shadow duration-300">
                <div class="flex justify-between items-center mb-2">
                    <h3 class="text-sm font-medium flex items-center">
                        <i class="fas ${indicator.icon} indicator-icon text-blue-500"></i>
                        ${indicator.title}
                    </h3>
                    <i class="fas ${indicator.trend === 'up' ? 'fa-arrow-up text-green-500' : indicator.trend === 'down' ? 'fa-arrow-down text-red-500' : 'fa-minus text-gray-500'}"></i>
                </div>
                <div class="text-2xl font-bold ${indicator.trend === 'up' ? 'text-green-600' : indicator.trend === 'down' ? 'text-red-600' : 'text-gray-800'}">${indicator.value}</div>
            </div>`;
        indicatorsContainer.insertAdjacentHTML('beforeend', indicatorHtml);
    });
}

// Update news
function updateNews(data) {
    const newsContainer = document.getElementById('news-items');
    newsContainer.innerHTML = ''; // Clear existing content

    if (data.news && Array.isArray(data.news) && data.news.length > 0) {
        // Display only the first 10 news items
        data.news.slice(0, 10).forEach(item => {
            const newsHtml = `
                <div class="w-[300px] flex-shrink-0 bg-white p-4 rounded-lg shadow-md hover:shadow-lg transition-shadow duration-300">
                    <a href="${item.link || '#'}" target="_blank" rel="noopener noreferrer" class="block">
                        <img src="${item.image || '/static/images/placeholder-image.jpg'}" alt="${item.headline}" class="w-full h-40 object-cover mb-2 rounded">
                        <h3 class="text-sm font-semibold mb-2 hover:text-blue-600 transition-colors duration-300">${item.headline || 'No headline'}</h3>
                        <p class="text-xs text-gray-500 mb-2">${item.summary || 'No summary available'}</p>
                        <p class="text-xs text-gray-400 flex items-center">
                            <i class="fas fa-newspaper mr-1"></i>
                            ${item.source || 'Unknown source'} - ${item.date ? new Date(item.date).toLocaleDateString() : 'No date'}
                        </p>
                    </a>
                </div>`;
            newsContainer.insertAdjacentHTML('beforeend', newsHtml);
        });
    } else {
        newsContainer.innerHTML = '<p class="text-red-500">No news available at the moment.</p>';
    }
}

function renderMarkdown(text) {
    // Hapus indentasi di awal pesan dan trim whitespace
    text = text.trim();
    
    // Ganti ## dengan h2 tag
    text = text.replace(/^##\s(.+)$/gm, '<h2 class="text-xl font-bold my-2">$1</h2>');
    
    // Ganti # dengan h1 tag
    text = text.replace(/^#\s(.+)$/gm, '<h1 class="text-2xl font-bold my-3">$1</h1>');
    
    // Ganti ** ** dengan strong tag
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Ganti * * dengan em tag
    text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // Ganti newline dengan <br> tag
    text = text.replace(/\n/g, '<br>');
    
    // Ganti - dengan list item
    text = text.replace(/^-\s(.+)$/gm, '<li>$1</li>');
    
    // Wrap list items dengan ul tag
    text = text.replace(/<li>(.|\n)*?(<\/li>)/g, '<ul class="list-disc list-inside my-2">$&</ul>');
    
    return text;
}

function showChatLoading() {
    document.getElementById('chat-loading').style.display = 'block';
}

function hideChatLoading() {
    document.getElementById('chat-loading').style.display = 'none';
}

function sendAIQuestion() {
    const questionInput = document.getElementById('ai-question');
    const question = questionInput.value;

    if (!question.trim()) return; // Jangan kirim jika pertanyaan kosong

    showChatLoading(); // Tampilkan loading di dalam card chat
    fetch(`${API_BASE_URL}/ai-recommendation`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            question: question, 
            session_id: sessionId,
            economic_data: globalEconomicData // Send stored economic data
        })
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            const chatHistory = document.getElementById('chat-history');
            
            if (data.chat_history && Array.isArray(data.chat_history)) {
                // Hanya tambahkan pesan baru, bukan mengganti seluruh riwayat
                const newMessages = data.chat_history.slice(-2); // Ambil 2 pesan terakhir (pertanyaan user dan jawaban AI)
                newMessages.forEach(message => {
                    const messageHtml = `
                        <div class="chat-message ${message.role === 'user' ? 'user-message' : 'assistant-message'}">
                            ${renderMarkdown(message.content)}
                        </div>`;
                    chatHistory.insertAdjacentHTML('beforeend', messageHtml);
                });

                // Scroll to the bottom of the chat history
                chatHistory.scrollTop = chatHistory.scrollHeight;
            } else {
                chatHistory.innerHTML += '<p class="text-red-500">Error: Invalid response from AI service.</p>';
            }

            // Clear the input field after sending the question
            questionInput.value = '';
            hideChatLoading(); // Sembunyikan loading
        })
        .catch(error => {
            console.error('Error sending AI question:', error);
            const chatHistory = document.getElementById('chat-history');
            chatHistory.innerHTML += `<p class="text-red-500">Error sending AI question: ${error.message}</p>`;
            hideChatLoading(); // Sembunyikan loading bahkan jika terjadi error
        });
}

// Function to display AI welcome message
function displayWelcomeMessage() {
    const chatHistory = document.getElementById('chat-history');
    const welcomeMessage = `
        <div class="chat-message assistant-message">
            Selamat datang di FOR/TRIX AI Trading Assistant! Saya siap membantu Anda dengan analisis dan rekomendasi trading forex USD/IDR. Silakan ajukan pertanyaan atau minta saran tentang kondisi pasar saat ini.
        </div>`;
    chatHistory.innerHTML = welcomeMessage;
}

function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    // Perbarui chart jika perlu
    if (chart) {
        chart.update();
    }
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    // Generate a new session ID when the page loads
    sessionId = generateSessionId();
    console.log("New session ID:", sessionId);

    // Display welcome message
    displayWelcomeMessage();

    document.getElementById('send-question').addEventListener('click', sendAIQuestion);

    document.getElementById('ai-question').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendAIQuestion();
        }
    });

    const historicalDaysSelect = document.getElementById('historical-days');
    const forecastDaysSelect = document.getElementById('forecast-days');

    historicalDaysSelect.addEventListener('change', (event) => {
        const historicalDays = parseInt(event.target.value);
        updateChart(globalHistoricalData, globalPredictions, parseInt(forecastDaysSelect.value), historicalDays);
    });

    forecastDaysSelect.addEventListener('change', async (event) => {
        const forecastDays = parseInt(event.target.value);
        if (lstmModel) {
            globalPredictions = await predictFuture(lstmModel, globalEconomicData.usdidr_data.slice(-5), forecastDays);
            updateChart(globalHistoricalData, globalPredictions, forecastDays, parseInt(historicalDaysSelect.value));
        } else {
            await fetchEconomicIndicators(forecastDays);
        }
    });

    // Initial load
    console.log("Initial load starting");
    fetchAllData()
        .catch(error => {
            console.error('Error during initial load:', error);
        });

    const darkModeToggle = document.getElementById('dark-mode-toggle');
    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', toggleDarkMode);
    }
    
    // Tambahkan event listener untuk responsivitas
    window.addEventListener('resize', () => {
        if (chart) {
            chart.resize();
        }
    });

    // Add hover effects to economic indicators
    const economicIndicators = document.getElementById('economic-indicators');
    economicIndicators.addEventListener('mouseover', (event) => {
        const indicator = event.target.closest('.bg-white');
        if (indicator) {
            indicator.classList.add('transform', 'scale-105', 'transition-transform', 'duration-300');
        }
    });
    economicIndicators.addEventListener('mouseout', (event) => {
        const indicator = event.target.closest('.bg-white');
        if (indicator) {
            indicator.classList.remove('transform', 'scale-105', 'transition-transform', 'duration-300');
        }
    });
});
