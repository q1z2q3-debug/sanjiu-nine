import json
from .dimensions import DimensionRegistry

ENCODE_SYSTEM_PROMPT = """你是「九维状态评估器」。
对给定上下文，评估它在每一维上的状态。
每维只能取 -1、0、+1。输出严格 JSON：
{"states": {"1": -1, "2": 0, ..., "9": 1}, "confidence": {"1": 0.9, ...}, "note": "50字内"}
"""

class CognitiveEncoder:
    def __init__(self, registry: DimensionRegistry, client=None, model="deepseek-chat"):
        self.registry = registry
        self.client = client
        self.model = model

    # ---------- 核心 ----------
    def encode_once(self, context: str) -> dict:
        if self.client is None:
            return self._mock_encode(context)
        dims = self.registry.get()
        dim_text = "\n".join(
            f"{d['id']}. {d['name']} —— {d['question']}\n"
            f"   -1: {d['states']['-1']}\n    0: {d['states']['0']}\n   +1: {d['states']['+1']}"
            for d in dims
        )
        user = f"【九维坐标系】\n{dim_text}\n\n【待评估上下文】\n{context}"
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": ENCODE_SYSTEM_PROMPT},
                      {"role": "user", "content": user}],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        return json.loads(resp.choices[0].message.content)

    def encode(self, context: str, n_runs: int = 1) -> dict:
        from collections import Counter
        runs = [self.encode_once(context) for _ in range(n_runs)]
        final, conf = {}, {}
        for i in range(1, 10):
            key = str(i)
            votes = [r["states"][key] for r in runs]
            winner, count = Counter(votes).most_common(1)[0]
            final[key] = winner
            conf[key] = count / n_runs
        return {
            "states": final,
            "vote_confidence": conf,
            "encoding": self.to_address(final),
        }

    # ---------- 编码工具 ----------
    @staticmethod
    def to_trit(states: dict) -> str:
        return "".join(str(states[str(i)] + 1) for i in range(1, 10))

    @staticmethod
    def to_decimal(trit: str) -> int:
        return int(trit, 3)

    @staticmethod
    def from_decimal(decimal: int) -> str:
        assert 0 <= decimal < 3**9
        s = ""
        n = decimal
        for _ in range(9):
            s = str(n % 3) + s
            n //= 3
        return s

    @classmethod
    def to_address(cls, states: dict) -> dict:
        trit = cls.to_trit(states)
        decimal = cls.to_decimal(trit)
        return {"trit": trit, "decimal": decimal, "hex_id": f"0x{decimal:04X}"}

    @staticmethod
    def hamming(a: str, b: str) -> int:
        return sum(1 for x, y in zip(a, b) if x != y)

    @staticmethod
    def weighted_hamming(a: str, b: str, weights: list[float] | None = None) -> float:
        """各向异性距离：每维按权重计入差异。weights 缺省时回退为等权 hamming/9。"""
        if not weights:
            return CognitiveEncoder.hamming(a, b)
        diff = 0.0
        wsum = 0.0
        for x, y, w in zip(a, b, weights):
            wsum += w
            if x != y:
                diff += w
        return diff / wsum if wsum else 0.0

    @staticmethod
    def neighbors(trit: str) -> list[str]:
        out = []
        for i in range(9):
            for v in "012":
                if v != trit[i]:
                    out.append(trit[:i] + v + trit[i+1:])
        return out

    # ---------- Mock ----------
    @staticmethod
    def _mock_encode(context: str) -> dict:
        import random
        rng = random.Random(hash(context) & 0xffffffff)
        states = {str(i): rng.choice([-1, 0, 1]) for i in range(1, 10)}
        return {
            "states": states,
            "confidence": {str(i): 0.7 for i in range(1, 10)},
            "note": "mock",
        }
