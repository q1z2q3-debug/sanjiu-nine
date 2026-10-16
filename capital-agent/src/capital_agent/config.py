import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    llm_provider: str = os.getenv("LLM_PROVIDER", "mock")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_base_url: str = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
    llm_model: str = os.getenv("LLM_MODEL", "deepseek-chat")

    embed_provider: str = os.getenv("EMBED_PROVIDER", "hash")
    embed_model: str = os.getenv("EMBED_MODEL", "text-embedding-3-small")

    confidence_threshold: float = float(os.getenv("AGENT_CONFIDENCE_THRESHOLD", "0.75"))
    explore_budget: int = int(os.getenv("AGENT_EXPLORE_BUDGET", "3"))

    db_path: str = os.getenv("DB_PATH", "capital.db")
    dims_path: str = os.getenv("DIMS_PATH", "dimensions.json")
    policy_path: str = os.getenv("POLICY_PATH", "local_policy.npz")

    def is_real_llm(self) -> bool:
        return self.llm_provider != "mock" and bool(self.llm_api_key)
