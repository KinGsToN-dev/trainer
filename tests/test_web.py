import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_home_page(client):
    response = client.get('/')
    assert response.status_code == 200
    assert "Универсальный Тренажер".encode('utf-8') in response.data

def test_profile_page(client):
    response = client.get('/profile')
    assert response.status_code == 200
    assert "Профиль".encode('utf-8') in response.data

def test_code_runner_page(client):
    response = client.get('/code_runner')
    assert response.status_code == 200
    assert b"main.py" in response.data

def test_export_endpoint(client):
    response = client.get('/export')
    assert response.status_code == 200
    # ИСПРАВЛЕНИЕ: Проверяем, что в типе есть слово "zip" (подходит и для Windows, и для Linux)
    assert "zip" in response.mimetype.lower()
    assert b"PK" in response.data[:2]
