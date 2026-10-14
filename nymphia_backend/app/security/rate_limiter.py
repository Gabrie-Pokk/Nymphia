import os
import time
from collections import defaultdict
from threading import Lock
from typing import Dict, List

class InMemoryRateLimiter:
    """
    Limitador de taxa por IP em memória com janela deslizante (sliding window).
    Protege endpoints de autenticação contra força bruta e exaustão de CPU por bcrypt.
    """
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = defaultdict(list)
        self.lock = Lock()

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        with self.lock:
            cutoff = now - self.window_seconds
            # Limpa timestamps expirados
            valid_timestamps = [t for t in self.requests[key] if t > cutoff]
            if len(valid_timestamps) >= self.max_requests:
                self.requests[key] = valid_timestamps
                return False
            valid_timestamps.append(now)
            self.requests[key] = valid_timestamps
            return True

    def reset(self):
        with self.lock:
            self.requests.clear()

auth_rate_limiter = InMemoryRateLimiter(
    max_requests=int(os.getenv("AUTH_RATE_LIMIT", "10")),
    window_seconds=int(os.getenv("AUTH_RATE_WINDOW_SECONDS", "60"))
)
