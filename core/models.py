from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Task:
    id: str
    module: str
    topic: str
    type: str
    prompt: str
    answer_spec: str
    difficulty: int = 1
    tags: list[str] = field(default_factory=list)

@dataclass
class ReviewState:
    task_id: str
    ease: float = 2.5
    interval_days: int = 0
    due_date: str = ""  # YYYY-MM-DD
    lapses: int = 0
    streak: int = 0

@dataclass
class Attempt:
    task_id: str
    timestamp: datetime
    user_answer: str
    correct: bool

@dataclass
class Result:
    correct: bool
    feedback: str
