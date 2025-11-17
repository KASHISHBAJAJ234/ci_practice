from app import app

# Feature test: test the weather API endpoint end-to-end (without redis/mongo)
def test_weather_feature():
    client = app.test_client()
    r = client.get("/weather?city=Delhi")
    assert r.status_code == 200
    assert "data" in r.json
