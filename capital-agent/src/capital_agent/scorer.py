import numpy as np
from .encoder import CognitiveEncoder
from .types import Weights

class GoalScorer:
    def __init__(self, weights: Weights = None, target_trit=None,
                 memory=None, learned_reward=None,
                 axis_weights: list[float] | None = None):
        self.w = (weights or Weights()).normalized()
        self.target = target_trit
        self.memory = memory
        self.learned = learned_reward
        self.axis_weights = axis_weights
        self._pot_cache: dict[str, dict[str, float]] = {}

    def address_score(self, trit):
        if not self.target:
            return 0.5
        return 1.0 - CognitiveEncoder.weighted_hamming(trit, self.target, self.axis_weights)

    def positive_score(self, trit):
        vals = [int(c) - 1 for c in trit]
        return (sum(vals) + 9) / 18.0

    def coherence_score(self, trit):
        vals = [int(c) - 1 for c in trit]
        return max(0.0, 1.0 - float(np.std(vals)))

    def potential_score(self, trit):
        if not self.memory:
            return 0.5
        if trit not in self._pot_cache:
            rows = self.memory.transition_map(from_trit=trit)
            self._pot_cache[trit] = {r["to"]: r["prob"] for r in rows}
        probs = self._pot_cache[trit]
        if not probs:
            return 0.5
        avg = sum(probs.values()) / len(probs)
        mx = max(probs.values())
        return 0.5 * avg + 0.5 * mx

    def learned_score(self, trit):
        if not self.learned:
            return 0.5
        return float(self.learned.score(trit))

    def score(self, trit):
        w = self.w
        s = (w.address * self.address_score(trit)
             + w.positive * self.positive_score(trit)
             + w.coherence * self.coherence_score(trit)
             + w.potential * self.potential_score(trit))
        if self.learned:
            s = 0.7 * s + 0.3 * self.learned_score(trit)
        return float(s)

    def explain(self, trit):
        return {
            "trit": trit,
            "address": round(self.address_score(trit), 4),
            "positive": round(self.positive_score(trit), 4),
            "coherence": round(self.coherence_score(trit), 4),
            "potential": round(self.potential_score(trit), 4),
            "total": round(self.score(trit), 4),
        }
