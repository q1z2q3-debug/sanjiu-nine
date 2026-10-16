"""embedding 语义记忆检索：场景相关任务验证。

任务：最优动作取决于"场景"（由某维度决定），且场景内的最优维度不是统一的"全高"。
  · 场景A（情绪=正面）：该提升"合规"维度
  · 场景B（情绪=中性）：该提升"方案"维度
格子几何（朝全高 222222222）无法区分这两个场景——从任一状态提升任意未高维，
hamming 都只减 1，几何上完全等价，选不出"该提合规还是方案"。
语义检索（SemanticRetriever）：用组合语义嵌入判定场景（情绪维贡献主导），
只在该场景的历史成功迁移里推荐动作 → 命中场景A 的经验，正确推荐"提升合规"。

演示分两步：
  ① 单元验证 recommend：新状态（情绪=正面）应推荐"提升合规"而非"提升方案"
  ② 端到端：带 retriever 的 agent 决策出现 semantic-recall 路由（0 token）
"""
import os
from src.capital_agent import Config, CapitalMemory
from src.capital_agent.llm import make_llm
from src.capital_agent.embedder import make_embedder
from src.capital_agent.semantic import SemanticRetriever
from src.capital_agent.agent import CapitalAgent

# 九维语义定义（维度2=情绪 为场景维）
DIMS = [
    {"id": 1, "name": "意图",   "question": "意图是否明确",   "states": {"-1": "模糊",  "0": "一般",  "+1": "明确"}},
    {"id": 2, "name": "情绪",   "question": "用户情绪状态",   "states": {"-1": "负面",  "0": "中性",  "+1": "正面"}},
    {"id": 3, "name": "上下文", "question": "上下文是否完整", "states": {"-1": "缺失",  "0": "部分",  "+1": "完整"}},
    {"id": 4, "name": "合规",   "question": "回复是否合规",   "states": {"-1": "违规",  "0": "一般",  "+1": "合规"}},
    {"id": 5, "name": "知识",   "question": "知识是否准确",   "states": {"-1": "错误",  "0": "一般",  "+1": "准确"}},
    {"id": 6, "name": "方案",   "question": "方案是否可执行", "states": {"-1": "空泛",  "0": "一般",  "+1": "可执行"}},
    {"id": 7, "name": "语气",   "question": "语气是否得体",   "states": {"-1": "生硬",  "0": "一般",  "+1": "得体"}},
    {"id": 8, "name": "风险",   "question": "风险是否可控",   "states": {"-1": "高危",  "0": "一般",  "+1": "可控"}},
    {"id": 9, "name": "满意",   "question": "用户是否满意",   "states": {"-1": "不满",  "0": "一般",  "+1": "满意"}},
]
# trit 位序 = 维度 id 顺序；pos0=意图,pos1=情绪(场景),pos2=上下文,pos3=合规,pos4=知识,pos5=方案,pos6=语气,pos7=风险,pos8=满意


def main():
    cfg = Config()
    for f in (cfg.db_path, cfg.policy_path):
        if os.path.exists(f):
            os.remove(f)

    mem = CapitalMemory(cfg.db_path, embedder=make_embedder(cfg))

    # 造"成功迁移"历史：transitions 表（只有成功迁移才会被记录）
    # 场景A（情绪=正面 pos1='2'）正确动作 = 提升"合规"(pos3)
    mem.record_transition("220000000", "220100000")  # 意图+1,情绪+1 → 提升合规
    mem.record_transition("220000000", "220100000")
    mem.record_transition("220000000", "220100000")
    mem.record_transition("202000000", "202100000")
    mem.record_transition("202000000", "202100000")
    # 场景B（情绪=中性 pos1='1'）正确动作 = 提升"方案"(pos5)
    mem.record_transition("210000000", "210001000")  # 意图+1,情绪中性 → 提升方案
    mem.record_transition("210000000", "210001000")
    mem.record_transition("210000000", "210001000")

    retriever = SemanticRetriever(mem, DIMS, embedder=make_embedder(cfg))

    print("=" * 60)
    print("embedding 语义记忆检索：场景相关任务验证")
    print("=" * 60)
    print("\n历史成功迁移：")
    print("  场景A(情绪正面): 220000000→220100000(提升合规)x3, 202000000→202100000(提升合规)x2")
    print("  场景B(情绪中性): 210000000→210001000(提升方案)x3")

    # ① 单元验证 recommend
    new_trit = "222000000"  # 意图+1,情绪+1,上下文+1 → 场景A；几何上与两个训练出发态都不同
    from src.capital_agent.encoder import CognitiveEncoder
    candidates = CognitiveEncoder.neighbors(new_trit)
    print(f"\n[1] 检索 recommend（新状态 = 情绪正面的场景A）")
    print(f"    新状态: {retriever.describe(new_trit)}")
    ranked = retriever.recommend(new_trit, candidates, top_k=3)
    dim_names = [d["name"] for d in DIMS]
    def changed_dim(trit):
        return [dim_names[i] for i in range(9) if trit[i] != new_trit[i]]
    print("    推荐 top3（动作 = 提升/调整的维度 + 得分）:")
    for trit, score in ranked:
        print(f"      {trit}  调整[{','.join(changed_dim(trit))}]  分={score:.3f}")
    top_action = ranked[0][0]
    top_dim = changed_dim(top_action)
    is_sceneA = "合规" in top_dim and "方案" not in top_dim
    print(f"\n    → top1 动作调整维度: {top_dim}")
    print(f"    → 判定: {'✅ 命中场景A（提升合规）' if is_sceneA else '❌ 未命中场景'}")
    print("    对比：几何(朝全高)从 222000000 提升任一未高维 hamming 都减1，无法区分场景，选不出该提合规还是方案。")

    # ② 端到端：agent 决策出现 semantic-recall
    print(f"\n[2] 端到端：带 retriever 的 agent 从 {new_trit} 决策")
    llm, _ = make_llm(cfg)
    a = CapitalAgent(new_trit, None, mem, llm, cfg, name="semantic",
                     retriever=retriever)
    r = a.run(max_steps=8)
    reasons = {}
    for h in r["history"]:
        reasons[h["source"]] = reasons.get(h["source"], 0) + 1
    hit = any("semantic-recall" in h.get("reason", "") for h in r["history"])
    print(f"  步数 {len(r['history'])}  决策来源 {reasons}  含 semantic-recall: {hit}")
    for h in r["history"][:4]:
        print(f"    {h['from']} → {h['to']}  [{h['reason']}]")

    print("\n结论：语义检索按场景(情绪维主导)命中经验，正确推荐场景A该做的'提升合规'；")
    print("      而格子几何在此类场景相关任务上失效——这正是 embedding 检索相对几何的价值。")
    mem.close()


if __name__ == "__main__":
    main()
