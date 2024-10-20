import os
from dotenv import load_dotenv
import google.generativeai as genai
import logging

# Load environment variables
load_dotenv()

# Configure the Google Gemini API with your API key from environment variable
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Configuration for the model generation
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
}

def generate_recommendation(fed_rate, bi_rate, inflation_id, inflation_us, current_jkse, current_sp500, current_usdidr, usdidr_1month_ago, predictions, news_text, user_question, history):
    try:
        logging.info("Generating recommendation")
        logging.info(f"Input data: fed_rate={fed_rate}, bi_rate={bi_rate}, inflation_id={inflation_id}, inflation_us={inflation_us}, current_jkse={current_jkse}, current_sp500={current_sp500}, current_usdidr={current_usdidr}, usdidr_1month_ago={usdidr_1month_ago}")
        logging.info(f"Predictions: {predictions}")
        logging.info(f"News text: {news_text}")
        logging.info(f"User question: {user_question}")

        # Define the system instruction with the input data
        system_instruction = f"""
        Kamu adalah pakar keuangan yang ramah dan berpengalaman. Tugasmu adalah membantu pengguna memahami situasi pasar valuta asing (forex) dan memberikan rekomendasi yang berdasarkan data dan berita terkini yang relevan.

        Berikut data yang tersedia:
        1. Suku bunga The Fed (AS): {fed_rate}%.
        2. Suku bunga Bank Indonesia (BI-7Day-RR): {bi_rate}%.
        3. Tingkat inflasi di Indonesia: {inflation_id}%.
        4. Tingkat inflasi di AS: {inflation_us}%.
        5. Harga penutupan terbaru Indeks Harga Saham Gabungan (JKSE): {current_jkse}.
        6. Harga penutupan terbaru S&P 500: {current_sp500}.
        7. Kurs USD/IDR saat ini: {current_usdidr}.
        8. Kurs USD/IDR satu bulan yang lalu: {usdidr_1month_ago}.
        9. Prediksi kurs USD/IDR untuk {len(predictions)} hari ke depan: {predictions}.
        10. Berita terkini yang relevan: {news_text}.

        Berdasarkan data dan berita terkini, lakukan hal berikut:
        1. Jelaskan bagaimana kondisi pasar saat ini dengan bahasa yang sederhana dan santai, mengacu pada data dan berita yang ada.
        2. Berikan rekomendasi apakah pengguna sebaiknya **membeli**, **menjual**, atau **menahan** transaksi USD/IDR.
        3. Berikan alasan dari rekomendasi tersebut, mengaitkan penjelasan dengan berita terbaru dan data pasar yang tersedia. Gunakan bahasa yang mudah dipahami dan hindari istilah keuangan yang terlalu teknis.

        **Catatan penting:**
        - Jika pertanyaan atau konteks di luar topik keuangan, valuta asing (forex), atau data yang diberikan, kamu **tidak boleh menjawab**.
        - Pastikan jawaban kamu selalu relevan dengan topik keuangan atau pasar forex yang dibahas.

        Pastikan rekomendasimu praktis, langsung ke intinya, dan mudah diikuti. Jika berita terkini menunjukkan situasi yang stabil atau tidak ada perubahan besar, sampaikan bahwa pengguna bisa menunggu sebelum mengambil keputusan.
        """
        
        # Initialize the model
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=generation_config,
            system_instruction=system_instruction
        )

        # Format history according to the expected structure
        formatted_history = []
        for message in history:
            if message['role'] == 'user':
                formatted_history.append({"role": "user", "parts": [{"text": message['content']}]})    
            elif message['role'] == 'assistant':
                formatted_history.append({"role": "model", "parts": [{"text": message['content']}]})

        # Create a chat session and pass the existing history
        chat = model.start_chat(history=formatted_history)

        # Send the user question to the model and get the response
        response = chat.send_message(f"{user_question}")
        
        # Add the new message to the history
        history.append({"role": "user", "content": user_question})
        history.append({"role": "assistant", "content": response.text})
        
        logging.info("Recommendation generated successfully")
        return history
    except Exception as e:
        logging.error(f"Error in generate_recommendation: {str(e)}", exc_info=True)
        return history + [{"role": "assistant", "content": "Maaf, terjadi kesalahan saat menghasilkan rekomendasi. Silakan coba lagi nanti."}]


# Function to generate an analysis report and quick recommendation
def generate_analysis_report_and_recommendation(fed_rate, bi_rate, inflation_id, inflation_us, current_jkse, current_sp500, current_usdidr, usdidr_1month_ago, predictions, news_text):
    try:
        system_instruction = f"""Anda adalah seorang pakar keuangan. Buat laporan singkat dalam bentuk paragraf dengan penekanan di beberapa poin penting, berdasarkan indikator berikut:
        - Suku Bunga Fed: {fed_rate}%
        - Suku Bunga BI: {bi_rate}%
        - Inflasi di Indonesia: {inflation_id}%
        - Inflasi di AS: {inflation_us}%
        - Indeks Harga Saham Gabungan (JKSE): {current_jkse}
        - Indeks S&P 500: {current_sp500}
        - Nilai tukar USD/IDR saat ini: {current_usdidr}
        - Nilai tukar USD/IDR 1 bulan lalu: {usdidr_1month_ago}
        - Prediksi harga USD/IDR: {predictions}
        - Berita terkait: {news_text}

        Jangan ulangi format di bawah ini. Cukup berikan **laporan singkat dalam bentuk paragraf** dengan penekanan pada poin penting seperti suku bunga, inflasi, dan prediksi harga. Gunakan tanda baca untuk memberikan penekanan, misalnya: *suku bunga meningkat* atau **prediksi penurunan**.

        Format yang diinginkan:
        1. LAPORAN SINGKAT: Berikan laporan dalam bentuk paragraf yang menghubungkan data, mencakup kondisi ekonomi dan pasar terkini, dan berikan penekanan pada poin-poin penting.
        2. REKOMENDASI CEPAT: Berikan rekomendasi cepat yang terkait dengan tindakan yang harus diambil, seperti membeli, menjual, atau menahan.
        """

        # Initialize the model
        model = genai.GenerativeModel(model_name="gemini-1.5-flash", generation_config=generation_config)

        # Send the instruction to the model and get the response
        response = model.generate_content(system_instruction)

        # Return the text response from the model
        return response.text
    except Exception as e:
        logging.error(f"Error generating AI report: {str(e)}", exc_info=True)
        return "Terjadi kesalahan saat menghasilkan laporan dan rekomendasi."
