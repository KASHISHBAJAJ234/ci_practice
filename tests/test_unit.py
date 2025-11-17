from app import app

# Unit test
def test_home():
    client = app.test_client()
    r = client.get("/")
    assert r.status_code == 200
    assert r.json["message"] == "Weather API is running!"
