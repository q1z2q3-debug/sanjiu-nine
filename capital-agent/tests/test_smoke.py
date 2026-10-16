from capital_agent.encoder import CognitiveEncoder
from capital_agent.memory import CapitalMemory
from capital_agent.llm import MockLLM
from capital_agent.agent import CapitalAgent
from capital_agent.config import Config
from capital_agent.distill import LocalPolicyModel
import os


def test_encode_roundtrip():
    states = {str(i): (i % 3) - 1 for i in range(1, 10)}
    addr = CognitiveEncoder.to_address(states)
    assert len(addr["trit"]) == 9
    assert CognitiveEncoder.from_decimal(addr["decimal"]) == addr["trit"]


def test_agent_run_and_graduate():
    if os.path.exists("test.db"):
        os.remove("test.db")
    mem = CapitalMemory("test.db")
    llm = MockLLM()
    cfg = Config(confidence_threshold=0.7, explore_budget=2)
    a = CapitalAgent("000000000", "222222222", mem, llm, cfg, name="t")
    r = a.run(max_steps=20)
    s = a.graduate_status()
    assert r["steps"] >= 0
    assert "autonomy_rate" in s
    mem.close()
    os.remove("test.db")


def test_distill():
    if os.path.exists("test2.db"):
        os.remove("test2.db")
    mem = CapitalMemory("test2.db")
    mem.upsert_policy("000000000", "100000000", "llm", True, 0.2)
    mem.upsert_policy("100000000", "200000000", "llm", True, 0.2)
    model = LocalPolicyModel(mem)
    rep = model.train(epochs=5)
    assert rep["trained"]
    mem.close()
    os.remove("test2.db")
