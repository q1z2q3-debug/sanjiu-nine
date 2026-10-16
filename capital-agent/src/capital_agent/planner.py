import heapq
from dataclasses import dataclass, field
from .encoder import CognitiveEncoder

@dataclass(order=True)
class _Node:
    priority: float
    trit: str = field(compare=False)

class PathPlanner:
    def __init__(self, scorer):
        self.scorer = scorer

    def astar_to_target(self, start, target):
        if start == target:
            return [start]
        heap = [_Node(0.0, start)]
        came = {}
        g = {start: 0}
        while heap:
            cur = heapq.heappop(heap).trit
            if cur == target:
                return self._reconstruct(came, cur)
            for nb in CognitiveEncoder.neighbors(cur):
                ng = g[cur] + 1
                if nb not in g or ng < g[nb]:
                    g[nb] = ng; came[nb] = cur
                    h = CognitiveEncoder.hamming(nb, target)
                    heapq.heappush(heap, _Node(ng + h, nb))
        raise ValueError(f"无路径 {start} → {target}")

    @staticmethod
    def _reconstruct(came, cur):
        path = [cur]
        while cur in came:
            cur = came[cur]; path.append(cur)
        return list(reversed(path))

    def hill_climb(self, start, max_steps=20, patience=3):
        cur = start
        cur_s = self.scorer.score(cur)
        path = [cur]; scores = [cur_s]
        no_improve = 0
        for _ in range(max_steps):
            best_nb, best_s = None, cur_s
            for nb in CognitiveEncoder.neighbors(cur):
                s = self.scorer.score(nb)
                if s > best_s:
                    best_nb, best_s = nb, s
            if best_nb is None:
                no_improve += 1
                if no_improve >= patience:
                    break
                continue
            cur, cur_s = best_nb, best_s
            path.append(cur); scores.append(cur_s)
            no_improve = 0
        return {"start": start, "end": cur, "path": path,
                "scores": [round(s, 4) for s in scores],
                "improvement": round(cur_s - self.scorer.score(start), 4),
                "steps": len(path) - 1}

    def beam_search(self, start, max_depth=12, beam_width=5):
        beam = [(self.scorer.score(start), [start])]
        best = beam[0]
        for _ in range(max_depth):
            cands = []
            for _, path in beam:
                for nb in CognitiveEncoder.neighbors(path[-1]):
                    if nb in path:
                        continue
                    cands.append((self.scorer.score(nb), path + [nb]))
            if not cands:
                break
            cands.sort(key=lambda x: -x[0])
            beam = cands[:beam_width]
            if beam[0][0] > best[0]:
                best = beam[0]
        return {"start": start, "end": best[1][-1], "path": best[1],
                "scores": [round(self.scorer.score(t), 4) for t in best[1]],
                "best_score": round(best[0], 4),
                "steps": len(best[1]) - 1}
