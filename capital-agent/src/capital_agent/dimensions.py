import json
import time
from pathlib import Path

import numpy as np

class DimensionRegistry:
    """冻结九维定义，支持持久化。每维可带语义锚定权重 weight（缺省 1.0）。"""

    def __init__(self, path: str = "dimensions.json"):
        self.path = Path(path)
        self.dimensions: list[dict] | None = None

    def register(self, dimensions: list[dict]):
        assert len(dimensions) == 9, f"必须 9 维，当前 {len(dimensions)}"
        for i, d in enumerate(dimensions, 1):
            assert d.get("id") == i
            assert set(d.get("states", {}).keys()) == {"-1", "0", "+1"}
            d.setdefault("weight", 1.0)
        self.dimensions = dimensions

    def save(self):
        self.path.write_text(json.dumps(self.dimensions, ensure_ascii=False, indent=2),
                             encoding="utf-8")

    def load(self):
        self.dimensions = json.loads(self.path.read_text(encoding="utf-8"))
        assert len(self.dimensions) == 9
        for d in self.dimensions:
            d.setdefault("weight", 1.0)
        return self.dimensions

    def get(self):
        assert self.dimensions is not None, "先 register 或 load"
        return self.dimensions

    def weights(self) -> list[float]:
        """返回每维语义锚定权重（各向异性距离用）。"""
        return [float(d.get("weight", 1.0)) for d in self.get()]

    def exists(self) -> bool:
        return self.path.exists()


class DimensionPool:
    """任务族 → 九维，支持多任务族共存。维度权重由语义锚定生成（学度量）。"""

    def __init__(self, memory, client=None, model="deepseek-chat", embedder=None):
        self.mem = memory
        self.client = client
        self.model = model
        from .embedder import HashEmbedder
        self.embedder = embedder or HashEmbedder()
        self.mem.conn.executescript("""
        CREATE TABLE IF NOT EXISTS dimension_sets (
            task_family TEXT PRIMARY KEY,
            dimensions  TEXT NOT NULL,
            created_at  REAL,
            usage_count INTEGER DEFAULT 0
        );
        """)
        self.mem.conn.commit()

    def get_or_create(self, task_family: str, seed_context: str) -> list[dict]:
        row = self.mem.conn.execute(
            "SELECT dimensions FROM dimension_sets WHERE task_family=?",
            (task_family,),
        ).fetchone()
        if row:
            self.mem.conn.execute(
                "UPDATE dimension_sets SET usage_count=usage_count+1 WHERE task_family=?",
                (task_family,),
            )
            self.mem.conn.commit()
            return json.loads(row["dimensions"])

        dims = self._generate(seed_context)
        dims = self.anchor_semantic_weights(dims, seed_context, self.embedder)
        self.mem.conn.execute(
            "INSERT INTO dimension_sets (task_family, dimensions, created_at) VALUES (?,?,?)",
            (task_family, json.dumps(dims, ensure_ascii=False), time.time()),
        )
        self.mem.conn.commit()
        return dims

    @staticmethod
    def anchor_semantic_weights(dims: list[dict], context: str, embedder) -> list[dict]:
        """学度量：每维权重 = 该轴语义向量与任务上下文的余弦相关性（各向异性拓扑）。

        相关性越高权重越大，映射到 [0.5, 1.5]。这样"相邻"由语义决定，而非固定等权。
        """
        ctx_vec = embedder.embed(context)
        scores = []
        for d in dims:
            text = f"{d['name']} {d['question']} {' '.join(d['states'].values())}"
            v = embedder.embed(text)
            na, nb = np.linalg.norm(v), np.linalg.norm(ctx_vec)
            scores.append(float(np.dot(v, ctx_vec) / (na * nb)) if na and nb else 0.0)
        lo, hi = min(scores), max(scores)
        rng = hi - lo
        for d, s in zip(dims, scores):
            d["weight"] = round(0.5 + 1.0 * (s - lo) / rng, 3) if rng > 1e-9 else 1.0
        return dims

    def _generate(self, context: str) -> list[dict]:
        if self.client is None:
            return self._mock_dims(context)
        try:
            from .prompts import META_PROMPT
        except Exception:
            return self._mock_dims(context)
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": META_PROMPT},
                {"role": "user", "content": context},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        return json.loads(resp.choices[0].message.content)["dimensions"]

    def _mock_dims(self, context: str) -> list[dict]:
        if any(k in context for k in ("代码", "编程", "开发")):
            names = ["需求","架构","实现","测试","调试","性能","可读","安全","维护"]
        elif any(k in context for k in ("客服", "对话", "问答")):
            names = ["意图","情绪","上下文","知识","政策","方案","语气","风险","满意"]
        elif any(k in context for k in ("科研", "研究", "实验")):
            names = ["问题","背景","假设","实验","数据","结论","局限","新颖","复现"]
        else:
            names = [f"维度{i}" for i in range(1, 10)]
        return [
            {"id": i, "name": n, "question": f"{n}如何",
             "states": {"-1": f"{n}低", "0": f"{n}中", "+1": f"{n}高"}}
            for i, n in enumerate(names, 1)
        ]
