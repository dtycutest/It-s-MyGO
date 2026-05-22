from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_login_and_profile():
    resp = client.post(
        "/auth/login",
        json={"code": "demo", "raw_data": "raw", "signature": "sig"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    token = body["data"]["access_token"]

    profile = client.get("/users/profile", headers={"Authorization": f"Bearer {token}"})
    assert profile.status_code == 200
    assert profile.json()["data"]["user_id"] == body["data"]["user_id"]


def test_product_search():
    resp = client.get("/products/search", params={"keyword": "iphone"})
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["code"] == 0
    results = payload["data"]["list"]
    assert results
    assert all("iphone" in item["title"].lower() for item in results)
