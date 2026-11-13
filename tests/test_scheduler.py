from core.scheduler import update_review_state
from core.models import ReviewState

def test_correct_answer_increases_interval():
    # Первый правильный ответ
    state = ReviewState(task_id="test", streak=0, interval_days=0)
    new_state = update_review_state(state, is_correct=True)
    assert new_state.streak == 1
    assert new_state.interval_days == 1

    # Второй правильный ответ
    new_state = update_review_state(new_state, is_correct=True)
    assert new_state.streak == 2
    assert new_state.interval_days == 6

def test_incorrect_answer_resets_interval():
    # Если ответили неверно, интервал сбрасывается на 1, стрик обнуляется
    state = ReviewState(task_id="test", streak=5, interval_days=20, lapses=0)
    new_state = update_review_state(state, is_correct=False)
    assert new_state.streak == 0
    assert new_state.interval_days == 1
    assert new_state.lapses == 1
