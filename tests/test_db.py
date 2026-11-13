import sqlite3
import pytest
from core import db
from core.models import ReviewState
from datetime import datetime

# Переопределяем файл БД для тестов, чтобы не ломать основную базу
@pytest.fixture(autouse=True)
def test_db(monkeypatch, tmp_path):
    test_db_file = tmp_path / "test_trainer.db"
    monkeypatch.setattr(db, "DB_FILE", str(test_db_file))
    db.init_db() # Создаем таблицы в тестовой базе

def test_save_and_get_review_state():
    # Сохраняем
    state = ReviewState(task_id="test_1", ease=2.5, interval_days=5, due_date="2024-01-01", lapses=1, streak=3)
    db.save_review_state(state)
    
    # Читаем
    fetched = db.get_review_state("test_1")
    assert fetched.task_id == "test_1"
    assert fetched.interval_days == 5
    assert fetched.streak == 3

def test_delete_task_progress():
    # Добавляем прогресс
    state = ReviewState(task_id="test_2", ease=2.5, interval_days=1, due_date="2024-01-01", lapses=0, streak=1)
    db.save_review_state(state)
    
    # Удаляем
    db.delete_task_progress("test_2")
    
    # Проверяем, что вернулось дефолтное состояние (due_date 2020-01-01)
    fetched = db.get_review_state("test_2")
    assert fetched.due_date == "2020-01-01"
