from core.models import Task, Result

class Module:
    name: str
    def load_tasks(self) -> list[Task]:
        raise NotImplementedError
    def check(self, task: Task, user_answer: str) -> Result:
        raise NotImplementedError
