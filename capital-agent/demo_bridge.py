# -*- coding: utf-8 -*-
"""演示：三元符号层读 capital-agent 认知状态。

跑一个朝目标前进的 agent，把决策轨迹每个状态译成卦，用象义/断辞注解——
证明"认知层状态 = 卦象，符号层作注解"的只读桥接成立。
"""
import os
from bridge import cognitive_oracle

from src.capital_agent import Config, CapitalMemory
from src.capital_agent.llm import make_llm
from src.capital_agent.agent import CapitalAgent

cfg = Config()
for f in (cfg.db_path, cfg.policy_path):
    if os.path.exists(f):
        os.remove(f)
mem = CapitalMemory(cfg.db_path)
llm, _ = make_llm(cfg)

START, GOAL = "111111111", "222222222"   # 全中和 → 全阳：朝目标单向推进
a = CapitalAgent(START, GOAL, mem, llm, cfg, name="bridge")
r = a.run(max_steps=6)

print("认知层决策轨迹 → 符号层卦象注解（只读桥接，不改认知层）\n")
for i, h in enumerate(r["history"]):
    o = cognitive_oracle(h["to"])
    src = h.get("reason") or h["source"]
    print(f"步{i+1}: {h['from']} → {h['to']}  [{src}]")
    print(f"  卦 idx{o['idx']}（等价组{o['group_rep_idx']}） 卦体{o['hexagram']}")
    print(f"  象义「{o['oracle']['name']}」{o['oracle']['statement']}")
    # 断辞须基于"动前"状态：这一步实际动的是 from 里的那个爻
    diff = [i for i in range(9) if h["from"][i] != h["to"][i]]
    if diff:
        fo = cognitive_oracle(h["from"])
        y = fo["yi"][diff[0]]
        print(f"  动爻断辞 {y['statement']}")
    print()
