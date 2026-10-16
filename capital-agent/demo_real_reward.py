"""真实奖励闭环演示：success 由任务评估器（业务规则）判定，而非格子几何。

三点接入的验证：
  1. 学度量    —— 语义锚定权重（各向异性，0.5~1.5），见 [1]
  2. 语义轴    —— 维度是真实业务语义（意图/情绪/…），见 [1]
  3. 真实奖励  —— reward 同时驱动"选动作"和"成功判定"；策略据此累积；
                 蒸馏模型以 0 Token 复现爬升。见 [2][3][4]

诚实说明：贪心探索 + 玩具 MLP 只能到达局部区域，不代表全局最优；
本演示验证的是"真实奖励闭环"的接线与价值（token 下放），而非优化器强度。
"""
import os
from src.capital_agent import Config, CapitalMemory, CapitalAgent, JudgedTask
from src.capital_agent.llm import make_llm
from src.capital_agent.embedder import make_embedder
from src.capital_agent.dimensions import DimensionRegistry, DimensionPool
from src.capital_agent.distill import LocalPolicyModel
from src.capital_agent.evolver import SelfEvolver
from src.capital_agent.swarm import SwarmCoordinator

# ---------- 真实评估器：可分离业务规则，与格子几何无关 ----------
ATTR = [
    ("意图明确", 1.2), ("情绪正面", 0.8), ("信息完整", 1.0),
    ("方案可执行", 1.1), ("政策合规", 1.3), ("语气得体", 0.7),
    ("风险可控", 1.2), ("知识准确", 1.1), ("用户满意", 1.0),
]

def judge(trit: str) -> float:
    vals = [int(c) - 1 for c in trit]
    return float(sum(w * v for v, (_, w) in zip(vals, ATTR)))


def main():
    cfg = Config()
    for f in (cfg.db_path, cfg.policy_path):
        if os.path.exists(f):
            os.remove(f)

    print("=" * 62)
    print("真实奖励闭环演示：success = 业务评估器，而非格子距离")
    print("=" * 62)

    mem = CapitalMemory(cfg.db_path, embedder=make_embedder(cfg))
    pool = DimensionPool(mem, embedder=make_embedder(cfg))
    dims = pool.get_or_create("客服回复", "客服回复质量优化")
    reg = DimensionRegistry(cfg.dims_path)
    reg.register(dims); reg.save()
    axis_w = reg.weights()

    # [1] 学度量 + 语义轴
    print("\n[1] 语义锚定权重（学度量）+ 语义轴")
    for d in dims:
        print(f"  {d['id']}. {d['name']:<6} 权重={d['weight']}")
    llm, _ = make_llm(cfg)
    task = JudgedTask("客服回复质量", judge_fn=judge)

    # [2] 真实奖励驱动的爬升（无模型，reward 同时选动作+判成功）
    print("\n[2] 真实奖励驱动的爬升（新手，无蒸馏模型）")
    a = CapitalAgent("000000000", None, mem, llm, cfg, name="A",
                     task=task, axis_weights=axis_w)
    r = a.run(max_steps=40)
    traj = [judge(h["from"]) for h in r["history"]][:14]
    src = {}
    for h in r["history"]:
        src[h["source"]] = src.get(h["source"], 0) + 1
    print("  奖励轨迹(每步):", " → ".join(f"{x:.1f}" for x in traj), "…")
    print(f"  结束态 {a.trit}  真实分 {judge(a.trit):.2f}（起点 {judge('000000000'):.2f}）")
    print(f"  决策来源 {src}  成功步数 {sum(1 for h in r['history'] if h['success'])}/{len(r['history'])}")

    # [3] 多 Agent 共享资本 + 真实奖励累积策略
    print("\n[3] 多 Agent 探索，策略按真实奖励累积")
    starts = ["000000000", "001000000", "000001000", "010000010",
              "000100100", "100000100", "000000001"]
    coord = SwarmCoordinator(mem, llm, cfg)
    coord.spawn(len(starts), starts[0], None, task_tag="real-reward")
    for ag, s in zip(coord.agents, starts):
        ag.trit = s
    coord.run(max_rounds=40)
    cov = mem.policy_coverage()
    rows = mem.conn.execute(
        "SELECT trit,action,success,total FROM policies ORDER BY total DESC LIMIT 3"
    ).fetchall()
    print(f"  策略覆盖 {cov['covered_states']} 状态 / {cov['total_policies']} 条")
    for r_ in rows:
        print(f"    策略 {r_['trit']} → {r_['action']}  success={r_['success']}/{r_['total']}")

    # [4] 蒸馏模型 0 Token 复现爬升
    print("\n[4] 进化 + 蒸馏（0 Token），蒸馏模型独立决策")
    evo = SelfEvolver(mem).evolve()
    model = LocalPolicyModel(mem)
    rep = model.train(epochs=120)
    model.save(cfg.policy_path)
    print(f"  进化: 新增{evo['new_policies']}/提升{evo['boosted_policies']}  "
          f"蒸馏样本{rep.get('samples')} 损失{rep.get('first_loss')}→{rep.get('final_loss')}")

    model2 = LocalPolicyModel(mem); model2.load(cfg.policy_path)
    bg = CapitalAgent("000000000", None, mem, llm, cfg, name="B-distilled",
                      local_model=model2, task=task, axis_weights=axis_w)
    rg = bg.run(max_steps=40)
    srcg = {}
    for h in rg["history"]:
        srcg[h["source"]] = srcg.get(h["source"], 0) + 1
    print(f"  结束态 {bg.trit}  真实分 {judge(bg.trit):.2f}")
    print(f"  决策来源 {srcg}  成功步数 {sum(1 for h in rg['history'] if h['success'])}/{len(rg['history'])}")

    # [5] 结论（诚实）
    print("\n" + "=" * 62)
    print("结论")
    print(f"  · 真实奖励同时驱动选动作与判成功，策略按真实分累积（[2][3]）")
    print(f"  · 蒸馏模型独立决策全为 local，0 Token 复现爬升（[4]）；全流程累计 {mem.token_stats()['total_tokens']} Token 主要来自 [2] 新手阶段的 LLM")
    print(f"  · 局限：贪心+玩具 MLP 到达局部区域（{judge(bg.trit):.2f} vs 全局 {judge('222222222'):.2f}），")
    print("    要逼近全局需更好的搜索/表示——这是下一步，不是本闭环的目标")
    mem.close()


if __name__ == "__main__":
    main()
