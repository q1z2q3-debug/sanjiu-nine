import hashlib
import numpy as np

class HashEmbedder:
    """本地稳定 hash 嵌入，无外部依赖。"""
    def __init__(self, dim: int = 64):
        self.dim = dim

    def embed(self, text: str) -> np.ndarray:
        h = hashlib.sha256(text.encode("utf-8")).digest()
        seed = int.from_bytes(h[:8], "little")
        rng = np.random.default_rng(seed)
        v = rng.standard_normal(self.dim).astype(np.float32)
        return v / (np.linalg.norm(v) + 1e-9)


class OpenAIEmbedder:
    def __init__(self, client, model: str = "text-embedding-3-small"):
        self.client = client
        self.model = model

    def embed(self, text: str) -> np.ndarray:
        r = self.client.embeddings.create(model=self.model, input=text)
        v = np.array(r.data[0].embedding, dtype=np.float32)
        return v / (np.linalg.norm(v) + 1e-9)


def make_embedder(cfg, client=None):
    if cfg.embed_provider == "openai" and client:
        return OpenAIEmbedder(client, cfg.embed_model)
    return HashEmbedder()
