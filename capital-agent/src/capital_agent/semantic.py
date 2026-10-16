"""组合语义嵌入 + 场景相关的动作检索。

核心思想：
  格子几何的局限是"所有维度同等重要、距离各向同性"。这里给每维配一个语义向量
  （由维度定义的文本嵌入），一个状态的语义表示 = Σ(每维状态值 × 该维语义向量)。
  这样"场景相似"由语义决定，能跨格子几何泛化：在状态 A 学到的成功动作，
  可迁移到语义相近但几何相距较远的状态 B。

  recommend(trit, candidates)：
    只在"出发态语义与当前相似"的历史成功迁移（transitions 表，全是成功迁移）里，
    按"动作语义"给候选加权。动作语义 = 它改变的维度向量（而非目标状态全局向量），
    这样同维动作跨状态复用，不会误把"降回历史状态"当成高分。
"""
import numpy as np


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    return float(np.dot(a, b) / (na * nb)) if na and nb else 0.0


class SemanticRetriever:
    def __init__(self, memory, dims, embedder=None):
        self.mem = memory
        self.dims = dims  # 九维语义定义（list[dict]，含 name/question/states）
        from .embedder import HashEmbedder
        self.embedder = embedder or HashEmbedder()
        # 每维语义向量：由该维的名称+问题+三态描述嵌入
        self.dim_vecs = [
            self.embedder.embed(
                f"{d['name']} {d['question']} {' '.join(d['states'].values())}")
            for d in dims
        ]
        self._cache = {}

    # ---------- 组合语义嵌入 ----------
    def state_embed(self, trit: str) -> np.ndarray:
        if trit in self._cache:
            return self._cache[trit]
        v = np.zeros_like(self.dim_vecs[0])
        for i, c in enumerate(trit[:9]):
            v += (int(c) - 1) * self.dim_vecs[i]
        n = np.linalg.norm(v)
        v = v / n if n else v
        self._cache[trit] = v
        return v

    @staticmethod
    def _changed_axis(a: str, b: str) -> int | None:
        diff = [i for i in range(9) if a[i] != b[i]]
        return diff[0] if len(diff) == 1 else None

    # ---------- 场景相关的动作检索 ----------
    def recommend(self, trit, candidates, scene_threshold=0.3,
                  top_k=3, min_count=1):
        cur = self.state_embed(trit)
        # 每个候选动作 → 它改变的维度（动作语义）
        cand_axis = {}
        for c in candidates:
            ax = self._changed_axis(trit, c)
            if ax is not None:
                cand_axis[c] = ax
        if not cand_axis:
            return []

        rows = self.mem.conn.execute(
            "SELECT from_trit,to_trit,count FROM transitions").fetchall()
        # 只保留"出发态与当前场景语义相似"的成功迁移
        scene = []
        for r in rows:
            if r["count"] < min_count:
                continue
            sim = _cosine(cur, self.state_embed(r["from_trit"]))
            if sim >= scene_threshold:
                scene.append((sim, r))
        if not scene:
            return []

        # 动作语义 = 该迁移改变的维度向量；同维同向动作余弦=1，异维由语义相关性决定
        scores = {c: 0.0 for c in candidates}
        for sim, r in scene:
            j = self._changed_axis(r["from_trit"], r["to_trit"])
            if j is None:
                continue
            # 迁移方向：升(+)/降(-)，只匹配同方向的候选，避免振荡
            dir_j = 1 if int(r["to_trit"][j]) > int(r["from_trit"][j]) else -1
            w = r["count"] * sim
            for c, i in cand_axis.items():
                dir_i = 1 if int(c[i]) > int(trit[i]) else -1
                if dir_i != dir_j:
                    continue
                scores[c] += w * _cosine(self.dim_vecs[i], self.dim_vecs[j])

        # 聚合到"动作维度"：同一维多个候选（升/降到不同态）合并，避免并列干扰判定
        axis_scores = {}
        axis_best = {}
        for c, s in scores.items():
            ax = cand_axis[c]
            axis_scores[ax] = axis_scores.get(ax, 0.0) + s
            if ax not in axis_best or s > axis_best[ax][1]:
                axis_best[ax] = (c, s)
        ranked_axis = sorted(axis_scores.items(), key=lambda x: -x[1])
        return [(axis_best[ax][0], axis_best[ax][1])
                for ax, _ in ranked_axis[:top_k]]

    def describe(self, trit) -> str:
        """把 trit 转成可读的维度描述（便于演示）。"""
        parts = []
        for i, d in enumerate(self.dims[:9]):
            val = int(trit[i]) - 1
            label = {-1: d["states"]["-1"], 0: d["states"]["0"], 1: d["states"]["+1"]}[val]
            parts.append(f"{d['name']}={label}")
        return ", ".join(parts)
