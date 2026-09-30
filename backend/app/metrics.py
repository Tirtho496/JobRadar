from collections import Counter
from threading import Lock


class Metrics:
    def __init__(self) -> None:
        self._counters: Counter[str] = Counter()
        self._lock = Lock()

    def inc(self, name: str, amount: int = 1) -> None:
        with self._lock:
            self._counters[name] += amount

    def render(self) -> str:
        with self._lock:
            lines = [f"jobradar_{key} {value}" for key, value in sorted(self._counters.items())]
        return "\n".join(lines) + "\n"


metrics = Metrics()
