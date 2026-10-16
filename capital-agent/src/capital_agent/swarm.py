import numpy as np
from .agent import CapitalAgent
from .encoder import CognitiveEncoder

class SwarmCoordinator:
    def __init__(self, memory, llm, cfg=None, local_model=None):
        self.mem = memory
        self.llm = llm
        self.cfg = cfg
        self.local_model = local_model
        self.agents: list[CapitalAgent] = []

    def spawn(self, n, start, goal, task_tag="swarm"):
        agents = []
        for i in range(n):
            start_i = self._mutate(start, i)
            a = CapitalAgent(start_i, goal, self.mem, self.llm, self.cfg,
                             name=f"S{i}", local_model=self.local_model,
                             task_tag=task_tag)
            agents.append(a)
        self.agents = agents
        return agents

    @staticmethod
    def _mutate(trit, i):
        if i == 0:
            return trit
        prefix = int(trit[:2], 3)
        new_prefix = (prefix + i) % 9
        digits = ""
        v = new_prefix
        for _ in range(2):
            digits = str(v % 3) + digits
            v //= 3
        return digits + trit[2:]

    def run(self, max_rounds=40):
        for _ in range(max_rounds):
            alive = sum(1 for a in self.agents if a.step())
            if alive == 0:
                break
        return self.report()

    def report(self):
        results = []
        for a in self.agents:
            src = {}
            for h in a.history:
                src[h["source"]] = src.get(h["source"], 0) + 1
            results.append({
                "agent": a.name, "agent_id": a.agent_id,
                "start": a.history[0]["from"] if a.history else a.trit,
                "end": a.trit, "steps": len(a.history), "sources": src,
            })
        return {"agents": results, "coverage": self.mem.policy_coverage(),
                "tokens": self.mem.token_stats()}
