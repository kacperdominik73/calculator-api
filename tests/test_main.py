import pytest
from fastapi.testclient import TestClient

from app.main import APP_VERSION, app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data


def test_version():
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == APP_VERSION
    assert data["app"] == "calculator-api"


@pytest.mark.parametrize("op,a,b,expected", [
    ("add", 10, 5, 15),
    ("sub", 10, 5, 5),
    ("mul", 3, 4, 12),
    ("div", 10, 4, 2.5),
])
def test_calculate_operations(op, a, b, expected):
    response = client.post("/calculate", json={"operation": op, "a": a, "b": b})
    assert response.status_code == 200
    assert response.json()["result"] == expected


def test_calculate_div_by_zero():
    response = client.post("/calculate", json={"operation": "div", "a": 5, "b": 0})
    assert response.status_code == 400
    assert "zero" in response.json()["detail"].lower()


def test_calculate_unknown_operation():
    response = client.post("/calculate", json={"operation": "mod", "a": 5, "b": 2})
    assert response.status_code == 422


def test_calculate_invalid_type():
    response = client.post("/calculate", json={"operation": "add", "a": "x", "b": 2})
    assert response.status_code == 422
