"""端到端演示：从出生到毕业的全过程。"""
import os
from src.capital_agent import Config, CapitalMemory, CapitalAgent
from src.capital_agent.llm import make_llm
from src.capital_agent.embedder import make_embedder
from src.capital_agent.dimensions import DimensionRegistry, DimensionPool
from src.capital_agent.distill import LocalPolicyModel
from src.capital_agent.evolver import SelfEvolver
from src.capital_agent.swarm import SwarmCoordinator


def main():
    cfg = Config()
    for f in [cfg.db_path, cfg.policy_path]:
        if os.path.exists(f):
            os.remove(f)

    print("=" * 60)
    print("Capital Agent 端到端演示")
    print("=" * 60)

    # 1. 初始化
    print("\n[1] 初始化")
    mem = CapitalMemory(cfg.db_path, embedder=make_embedder(cfg))
    pool = DimensionPool(mem, embedder=make_embedder(cfg))
    dims = pool.get_or_create("demo", "Agent 认知架构")
    reg = DimensionRegistry(cfg.dims_path)
    reg.register(dims); reg.save()
    print(f"  九维已冻结，共 {len(dims)} 维")
    print("  语义锚定权重:", [d['weight'] for d in dims])

    llm, client = make_llm(cfg)
    start, goal = "000000000", "222222222"

    # 2. 单 Agent 学习
    print("\n[2] 单 Agent 学习（新生）")
    a1 = CapitalAgent(start, goal, mem, llm, cfg, name="A1")
    a1.run(max_steps=30)
    s1 = a1.graduate_status()
    print(f"  自主率: {s1['autonomy_rate']}  LLM 依赖: {s1['llm_dependency']}")
    print(f"  Token: {s1['token_spent']}  等级: {s1['level']}")

    # 3. 多 Agent 共享
    print("\n[3] 多 Agent 共享资本库")
    coord = SwarmCoordinator(mem, llm, cfg)
    coord.spawn(5, start, goal, task_tag="demo")
    coord.run(max_rounds=40)
    cov = mem.policy_coverage()
    print(f"  策略覆盖: {cov['covered_states']} 个状态")

    # 4. 自我进化
    print("\n[4] 自我进化（不花 Token）")
    evo = SelfEvolver(mem).evolve()
    print(f"  新增策略: {evo['new_policies']}  提升置信: {evo['boosted_policies']}")

    # 5. 蒸馏
    print("\n[5] 蒸馏本地模型")
    model = LocalPolicyModel(mem)
    rep = model.train(epochs=80)
    model.save(cfg.policy_path)
    print(f"  样本: {rep.get('samples')}  损失: {rep.get('first_loss')} → {rep.get('final_loss')}")

    # 6. 蒸馏模型独立跑
    print("\n[6] 蒸馏模型独立决策（0 Token）")
    model2 = LocalPolicyModel(mem); model2.load(cfg.policy_path)
    a2 = CapitalAgent(start, goal, mem, llm, cfg, name="distilled",
                     local_model=model2)
    r2 = a2.run(max_steps=30)
    s2 = a2.graduate_status()
    src = {}
    for h in r2["history"]:
        src[h["source"]] = src.get(h["source"], 0) + 1
    print(f"  到达目标: {r2['reached']}")
    print(f"  决策来源: {src}")
    print(f"  自主率: {s2['autonomy_rate']}  LLM 依赖: {s2['llm_dependency']}")
    print(f"  等级: {s2['level']}")

    # 7. 总览
    print("\n" + "=" * 60)
    print("总览")
    print("=" * 60)
    print(f"  记忆库: {mem.stats()}")
    print(f"  策略覆盖: {mem.policy_coverage()}")
    print(f"  Token 总消耗: {mem.token_stats()['total_tokens']}")
    mem.close()


if __name__ == "__main__":
    main()
