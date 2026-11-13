import pytest
from datetime import datetime, timedelta
from core import db
from core.models import Attempt

# Переопределяем БД для тестов
@pytest.fixture(autouse=True)
def test_db(monkeypatch, tmp_path):
    test_db_file = tmp_path / "test_trainer.db"
    monkeypatch.setattr(db, "DB_FILE", str(test_db_file))
    db.init_db()

def test_streak_calculation():
    # Пустая база - стрик 0
    assert db.get_streak() == 0

    # Добавляем попытку за сегодня
    db.save_attempt(Attempt("task1", datetime.now(), "ans", True))
    assert db.get_streak() == 1

    # Добавляем попытку за вчера
    yesterday = datetime.now() - timedelta(days=1)
    db.save_attempt(Attempt("task2", yesterday, "ans", True))
    assert db.get_streak() == 2

    # Добавляем попытку за 3 дня назад (пропуск дня) - стрик должен остаться 2
    three_days_ago = datetime.now() - timedelta(days=3)
    db.save_attempt(Attempt("task3", three_days_ago, "ans", True))
    assert db.get_streak() == 2
