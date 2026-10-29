
import pytest
from app import app, coupons


@pytest.fixture
def client():
    coupons.clear()
    app.config["TESTING"] = True

    with app.test_client() as test_client:
        yield test_client

    coupons.clear()


def create_coupon(client, **overrides):
    data = {
        "code": "SAVE10",
        "discount": 10,
        "minimum_amount": 500,
        "expiry": "2099-12-31",
        "usage_limit": 2
    }
    data.update(overrides)
    return client.post("/coupons", json=data)


def test_home_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"VERSION 3" in response.data


def test_health(client):
    assert client.get("/health").json["version"] == "v3"


def test_create_coupon(client):
    assert create_coupon(client).status_code == 201


def test_validate_coupon(client):
    create_coupon(client)
    response = client.get("/coupons/SAVE10/validate")
    assert response.status_code == 200
    assert response.json["remaining_uses"] == 2


def test_expired_coupon(client):
    create_coupon(client, expiry="2000-01-01")
    response = client.get("/coupons/SAVE10/validate")
    assert response.status_code == 400


def test_minimum_purchase(client):
    create_coupon(client)
    response = client.post(
        "/coupons/SAVE10/apply",
        json={"amount": 100}
    )
    assert response.status_code == 400


def test_usage_limit(client):
    create_coupon(client, usage_limit=1)

    first = client.post(
        "/coupons/SAVE10/apply",
        json={"amount": 1000}
    )
    assert first.status_code == 200
    assert first.json["remaining_uses"] == 0

    second = client.post(
        "/coupons/SAVE10/apply",
        json={"amount": 1000}
    )
    assert second.status_code == 400
    assert "usage limit" in second.json["error"].lower()


def test_duplicate_coupon(client):
    create_coupon(client)
    assert create_coupon(client).status_code == 409
