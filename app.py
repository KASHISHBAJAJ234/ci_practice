# app.py
import os
import time
import json
import requests
from flask import Flask, request, jsonify
import redis
from pymongo import MongoClient

app = Flask(__name__)

# -----------------------------
# CONNECT TO REDIS
# -----------------------------
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")   # localhost for local tests
redis_client = redis.Redis(host=REDIS_HOST, port=6379)

# -----------------------------
# CONNECT TO MONGODB
# -----------------------------
mongo_host = os.getenv("MONGO_HOST", "localhost")    # localhost for local tests
mongo_client = MongoClient(f"mongodb://{mongo_host}:27017/")
db = mongo_client["weatherdb"]
logs = db["logs"]

# -----------------------------
# CALL WEATHER API
# -----------------------------
def get_weather_from_api(city):
    url = f"https://wttr.in/{city}?format=j1"
    response = requests.get(url, timeout=5)
    return response.json()

# -----------------------------
# /weather ENDPOINT
# -----------------------------
@app.route("/weather")
def weather():
    city = request.args.get("city")
    if not city:
        return jsonify({"error": "city query parameter required"}), 400

    # --- REDIS CACHE CHECK ---
    cached = redis_client.get(city)
    if cached:
        cached = cached.decode("utf-8")      # bytes → string
        cached = json.loads(cached)          # string → dict
        return jsonify({"source": "redis", "data": cached})

    # --- CALL REAL API ---
    start = time.time()
    data = get_weather_from_api(city)
    latency = int((time.time() - start) * 1000)

    # Save dict → JSON string for Redis
    redis_client.setex(city, 60, json.dumps(data))

    # --- LOG IN MONGODB ---
    logs.insert_one({
        "city": city,
        "timestamp": time.time(),
        "latency_ms": latency,
        "source": "live",
        "weather": data
    })

    return jsonify({
        "source": "live",
        "latency_ms": latency,
        "data": data
    })

# -----------------------------
# / HOME ENDPOINT
# -----------------------------
@app.route("/")
def home():
    return jsonify({"message": "Weather API is running!"})

# -----------------------------
# RUN SERVER
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
