from datetime import datetime, timedelta
from core.models import ReviewState

def update_review_state(state: ReviewState, is_correct: bool) -> ReviewState:
    """Обновляет интервалы по алгоритму SM-2 (упрощенный)."""
    today = datetime.now().date()
    
    if is_correct:
        state.streak += 1
        if state.streak == 1:
            state.interval_days = 1
        elif state.streak == 2:
            state.interval_days = 6
        else:
            state.interval_days = round(state.interval_days * state.ease)
        # Небольшое увеличение легкости
        state.ease = min(2.5, state.ease + 0.1)
    else:
        state.streak = 0
        state.lapses += 1
        state.interval_days = 1
        # Штраф за ошибку
        state.ease = max(1.3, state.ease - 0.2)
        
    state.due_date = (today + timedelta(days=state.interval_days)).strftime("%Y-%m-%d")
    return state
