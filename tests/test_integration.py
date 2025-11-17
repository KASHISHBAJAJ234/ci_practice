import subprocess
import time
import requests

def test_integration_weather():
    # Start app
    process = subprocess.Popen(["python", "app.py"])
    time.sleep(2)  # wait for app to start

    try:
        r = requests.get("http://127.0.0.1:5000/weather?city=Delhi")
        assert r.status_code == 200
        assert "data" in r.json()
    finally:
        process.terminate()
