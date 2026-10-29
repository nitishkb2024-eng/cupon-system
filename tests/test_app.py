
import pytest
from app import app, coupons


@pytest.fixture
def client():
    coupons.clear()
    app.config["TESTING"] = True

    with app.test_client() as test_client:
        yield test_client

    coupons.clear()


def test_home_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Coupon" in response.data
    assert b"Studio" in response.data


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json["version"] == "v1"


def test_create_coupon(client):
    response = client.post(
        "/coupons",
        json={"code": "SAVE10", "discount": 10}
    )
    assert response.status_code == 201


def test_validate_coupon(client):
    client.post("/coupons", json={"code": "SAVE10", "discount": 10})

    response = client.get("/coupons/SAVE10/validate")
    assert response.status_code == 200
    assert response.json["valid"] is True


def test_apply_coupon(client):
    client.post("/coupons", json={"code": "SAVE10", "discount": 10})

    response = client.post(
        "/coupons/SAVE10/apply",
        json={"amount": 1000}
    )

    assert response.status_code == 200
    assert response.json["discount_amount"] == 100
    assert response.json["final_amount"] == 900


def test_duplicate_coupon(client):
    client.post("/coupons", json={"code": "SAVE10", "discount": 10})

    response = client.post(
        "/coupons",
        json={"code": "SAVE10", "discount": 20}
    )

    assert response.status_code == 409
