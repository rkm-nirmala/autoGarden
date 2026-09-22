from flask import Flask, request, jsonify
from dotenv import load_dotenv
import requests
import os

load_dotenv()

app = Flask(__name__)

sensor_data = {
    "suhu": None,
    "kelembapan": None,
    "soil": None,
    "cahaya": None
}


# =========================
# ESP32 -> Flask
# =========================

@app.route("/api/sensor", methods=["POST"])
def receive_sensor():

    data = request.get_json()

    if not data:
        return jsonify({
            "status": "error",
            "message": "Data JSON tidak ditemukan"
        }), 400

    sensor_data.update({
        "suhu": data.get("suhu"),
        "kelembapan": data.get("kelembapan"),
        "soil": data.get("soil"),
        "cahaya": data.get("cahaya")
    })

    print("Data sensor:", sensor_data)

    return jsonify({
        "status": "success",
        "data": sensor_data
    })


# =========================
# / -> Groq
# =========================

@app.route("/")
def home():

    # Pastikan sudah ada data dari ESP32
    if sensor_data["suhu"] is None:
        return """
        <h1>Monitoring ESP32</h1>
        <p>Belum ada data sensor dari ESP32.</p>
        """

    api_key = os.getenv("GROQ_API_KEY")

    prompt = f"""
    Kamu adalah AI yang menganalisis data sensor ESP32.

    Berikut data sensor terbaru:

    Suhu       : {sensor_data["suhu"]} °C
    Kelembapan : {sensor_data["kelembapan"]} %
    Soil       : {sensor_data["soil"]}
    Cahaya     : {sensor_data["cahaya"]}

    Analisis kondisi lingkungan berdasarkan data tersebut.

    Berikan:
    1. Kondisi suhu
    2. Kondisi kelembapan
    3. Kondisi tanah
    4. Kondisi cahaya
    5. Kesimpulan singkat
    6. Saran jika ada kondisi yang perlu diperhatikan

    Gunakan bahasa Indonesia yang mudah dipahami.
    """

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": "openai/gpt-oss-120b",
            "messages": [
                {
                    "role": "system",
                    "content": "Kamu adalah AI untuk monitoring IoT."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3
        },
        timeout=30
    )

    if response.status_code != 200:
        return f"""
        <h1>Gagal menghubungi Groq</h1>
        <pre>{response.text}</pre>
        """, 500

    result = response.json()

    answer = result["choices"][0]["message"]["content"]

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>ESP32 Monitoring</title>
        <meta charset="UTF-8">
    </head>

    <body>

        <h1>Monitoring ESP32</h1>

        <h2>Data Sensor</h2>

        <ul>
            <li>Suhu: {sensor_data["suhu"]} °C</li>
            <li>Kelembapan: {sensor_data["kelembapan"]} %</li>
            <li>Soil: {sensor_data["soil"]}</li>
            <li>Cahaya: {sensor_data["cahaya"]}</li>
        </ul>

        <h2>Analisis Groq</h2>

        <pre style="white-space: pre-wrap;">
{answer}
        </pre>

    </body>
    </html>
    """


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
