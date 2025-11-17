# app.py
import os
import time
import requests
from flask import Flask, request, jsonify
import redis
from pymongo import MongoClient

app = Flask(__name__)


# CONNECT TO REDIS
redis_host = os.environ.get("REDIS_HOST", "redis")
redis_client = redis.Redis(host=redis_host, port=6379, decode_responses=True)


# CONNECT TO MONGODB
mongo_host = os.environ.get("MONGO_HOST", "mongo")
mongo_client = MongoClient(f"mongodb://{mongo_host}:27017/")
db = mongo_client["weatherdb"]
logs = db["logs"]



# CALL WEATHER API

def get_weather_from_api(city):
    url = f"https://wttr.in/{city}?format=j1"
    response = requests.get(url, timeout=5)
    return response.json()



# /weather REST ENDPOINT
@app.route("/weather")
def weather():
    city = request.args.get("city", "Delhi")

    #CHECK REDIS CACHE
    cached = redis_client.get(city)
    if cached:
        return jsonify({"source": "redis", "data": cached})

    #  CALL REAL WEATHER API
    start = time.time()
    data = get_weather_from_api(city)
    latency = int((time.time() - start) * 1000)

    #  SAVE IN REDIS (expiry 60s)
    redis_client.set(city, str(data), ex=60)

    #  SAVE LOG IN MONGODB
    logs.insert_one({
        "city": city,
        "timestamp": time.time(),
        "latency": latency,
        "weather": data
    })

    #  RETURN WEATHER
    return jsonify({
        "source": "live",
        "latency_ms": latency,
        "data": data
    })


@app.route("/")
def home():
    return jsonify({"message": "Weather API is running!"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
