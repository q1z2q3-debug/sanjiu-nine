import argparse
import json
import sys

from .config import Config
from .dimensions import DimensionRegistry, DimensionPool
from .encoder import CognitiveEncoder
from .memory import CapitalMemory
from .llm import make_llm
from .embedder import make_embedder
from .agent import CapitalAgent
from .swarm import SwarmCoordinator
from .distill import LocalPolicyModel
from .evolver import SelfEvolver


def cmd_init(cfg):
    mem = CapitalMemory(cfg.db_path, embedder=make_embedder(cfg))
    pool = DimensionPool(mem, embedder=make_embedder(cfg))
    dims = pool.get_or_create("default", "通用认知任务")
    reg = DimensionRegistry(cfg.dims_path)
    reg.register(dims); reg.save()
    print(f"✅ 初始化完成：{cfg.db_path} / {cfg.dims_path}")
    for d in dims:
        print(f"  {d['id']}. {d['name']}  权重={d['weight']}")


def cmd_encode(cfg, text):
    mem = CapitalMemory(cfg.db_path, embedder=make_embedder(cfg))
    reg = DimensionRegistry(cfg.dims_path); reg.load()
    llm, client = make_llm(cfg)
    enc = CognitiveEncoder(reg, client, cfg.llm_model)
    r = enc.encode(text, n_runs=1)
    print(json.dumps(r, ensure_ascii=False, indent=2))


def cmd_run(cfg, start, goal, steps):
    mem = CapitalMemory(cfg.db_path, embedder=make_embedder(cfg))
    reg = DimensionRegistry(cfg.dims_path); reg.load()
    llm, _ = make_llm(cfg)
    agent = CapitalAgent(start, goal, mem, llm, cfg, name="cli",
                         task_tag="cli")
    r = agent.run(max_steps=steps)
    s = agent.graduate_status()
    print(json.dumps({"run": r, "graduation": s}, ensure_ascii=False, indent=2))


def cmd_swarm(cfg, n, start, goal):
    mem = CapitalMemory(cfg.db_path, embedder=make_embedder(cfg))
    reg = DimensionRegistry(cfg.dims_path); reg.load()
    llm, _ = make_llm(cfg)
    coord = SwarmCoordinator(mem, llm, cfg)
    coord.spawn(n, start, goal, task_tag="cli-swarm")
    report = coord.run()
    print(json.dumps(report, ensure_ascii=False, indent=2))


def cmd_distill(cfg):
    mem = CapitalMemory(cfg.db_path, embedder=make_embedder(cfg))
    model = LocalPolicyModel(mem)
    rep = model.train()
    model.save(cfg.policy_path)
    print(json.dumps(rep, ensure_ascii=False, indent=2))


def cmd_evolve(cfg):
    mem = CapitalMemory(cfg.db_path, embedder=make_embedder(cfg))
    evo = SelfEvolver(mem)
    print(json.dumps(evo.evolve(), ensure_ascii=False, indent=2))


def cmd_stats(cfg):
    mem = CapitalMemory(cfg.db_path, embedder=make_embedder(cfg))
    print(json.dumps({
        "memory": mem.stats(),
        "coverage": mem.policy_coverage(),
        "tokens": mem.token_stats(),
    }, ensure_ascii=False, indent=2))


def main():
    cfg = Config()
    p = argparse.ArgumentParser(prog="capital", description="Token as Capital Agent")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init", help="初始化九维与记忆库")

    pe = sub.add_parser("encode", help="编码一段文本")
    pe.add_argument("text")

    pr = sub.add_parser("run", help="跑一个 Agent")
    pr.add_argument("--start", required=True)
    pr.add_argument("--goal", default=None)
    pr.add_argument("--steps", type=int, default=30)

    ps = sub.add_parser("swarm", help="多 Agent 协同")
    ps.add_argument("--n", type=int, default=5)
    ps.add_argument("--start", required=True)
    ps.add_argument("--goal", default=None)

    sub.add_parser("distill", help="蒸馏本地模型")
    sub.add_parser("evolve", help="自我进化")
    sub.add_parser("stats", help="查看统计")

    args = p.parse_args()

    if args.cmd == "init":     cmd_init(cfg)
    elif args.cmd == "encode": cmd_encode(cfg, args.text)
    elif args.cmd == "run":    cmd_run(cfg, args.start, args.goal, args.steps)
    elif args.cmd == "swarm":  cmd_swarm(cfg, args.n, args.start, args.goal)
    elif args.cmd == "distill": cmd_distill(cfg)
    elif args.cmd == "evolve": cmd_evolve(cfg)
    elif args.cmd == "stats":  cmd_stats(cfg)


if __name__ == "__main__":
    main()
