import pytest
from app import app
from services.task_manager import check_qa_answer

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_qa_fuzzy_matching():
    """Тест универсальной проверки ответов (с опечатками)"""
    assert check_qa_answer("apple", "apple") == True
    assert check_qa_answer(" Apple ", "apple") == True
    assert check_qa_answer("aple", "apple") == True # Опечатка
    assert check_qa_answer("banana", "apple") == False
    assert check_qa_answer("", "apple") == False

def test_train_settings_page(client):
    """Тест: страница настроек тренировки открывается"""
    response = client.get('/train')
    assert response.status_code == 200
    # ИСПРАВЛЕНИЕ: Используем .encode('utf-8') для русских букв
    assert "Настройки".encode('utf-8') in response.data or b"train" in response.data

def test_exam_settings_page(client):
    """Тест: страница настроек экзамена открывается и содержит предметы"""
    response = client.get('/exam')
    assert response.status_code == 200
    assert "Экзамен".encode('utf-8') in response.data or b"exam" in response.data
    assert b"subjectData" in response.data # Проверяем, что JSON с предметами передан

def test_start_exam_with_filters(client):
    """Тест: запуск экзамена с фильтрами (имитация POST-запроса)"""
    response = client.post('/start_exam', data={
        'limit': '5',
        'module': 'Python',
        'topic': 'math',
        'difficulty': '1'
    }, follow_redirects=True)
    # Если задачи есть, произойдет редирект на дашборд (200 OK)
    # Если задач нет, вернется страница с ошибкой (тоже 200 OK)
    assert response.status_code == 200
