class SafetyLayer:
    def __init__(self, window: int = 6):
        self.forbidden: set[str] = set()
        self.window = window
        self._recent: list[str] = []

    def forbid(self, trit: str):
        self.forbidden.add(trit)

    def filter_candidates(self, candidates: list[str]) -> list[str]:
        return [c for c in candidates if c not in self.forbidden]

    def check(self, action: str) -> tuple[bool, str]:
        if action in self.forbidden:
            return False, "forbidden"
        self._recent.append(action)
        if len(self._recent) > self.window:
            self._recent.pop(0)
        if len(self._recent) == self.window and len(set(self._recent)) <= 2:
            return False, "loop"
        return True, "ok"
