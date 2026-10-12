import threading
import time
from collections import deque

class RateLimiter:
    """Limite de taxa simples, em memória, com janela deslizante.

    Permite no máximo `limit` eventos por `window` segundos para cada chave
    (ex.: chat_id ou IP). Vale só para este processo: reinícios zeram os
    contadores e, com vários workers, cada um conta separadamente.
    """

    def __init__(self, limit, window=60, max_keys=10_000, clock=time.monotonic):
        self.limit = limit
        self.window = window
        self.max_keys = max_keys
        self.clock = clock
        self._hits = {}
        self._lock = threading.Lock()

    def allow(self, key):
        """Registra um evento da chave. Devolve False se ela passou do limite."""
        now = self.clock()
        with self._lock:
            hits = self._hits.get(key)
            if hits is None:
                if len(self._hits) >= self.max_keys:
                    self._cleanup(now)
                hits = self._hits[key] = deque()
            while hits and hits[0] <= now - self.window:
                hits.popleft()
            if len(hits) >= self.limit:
                return False
            hits.append(now)
            return True

    def _cleanup(self, now):
        # Remove chaves sem eventos na janela; se ainda houver chaves demais
        # (ex.: muitos IPs diferentes), descarta as mais antigas
        for key in [k for k, h in self._hits.items() if not h or h[-1] <= now - self.window]:
            del self._hits[key]
        if len(self._hits) >= self.max_keys:
            oldest = sorted(self._hits, key=lambda k: self._hits[k][-1])
            for key in oldest[:len(oldest) // 2]:
                del self._hits[key]
