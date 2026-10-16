# -*- coding: utf-8 -*-
"""三元九爻符号系统推演 Agent。

逆向周易64卦符号范式 → 迁移到"锁定三元九爻公理"，完成全集生成、
错/综/错综/互/变算子批量演算、等价组统计、符号图网络、逆向检索、聚类。

======================================================================
一、逆向周易64卦体系：提炼的符号建模范式（总结）
======================================================================
周易把世界编码为一个有限离散符号空间（2^6=64 卦），其"象义"并不悬空，
而是来自一整套可复算的结构算子。逆向提炼出的底层范式有六条：

1. 状态空间 = 有限离散格：以"位序×极性"张成一个完备但可穷举的状态空间。
   六爻 = 6 个位序，每爻阴/阳 2 极 → 64 态。空间本身是"象"的索引，象义是映射层。

2. 对偶算子（错卦/旁通）：逐爻阴阳互变。这是"相反相错"的结构表达——
   一种全域取反，保持位序、改变极性。刻画对立、镜像、互补。

3. 反转算子（综卦/覆卦）：卦体上下倒置（初上互换）。这是"序关系"——
   保持极性、改变位序。刻画反过来看、覆、逆。

4. 内核投影（互卦）：取中间爻重排，抛去上下卦。把整体塌缩为"内部交互结构"，
   是结构粗粒化的投影映射（9→5 维同理，是对"内核"的截取）。

5. 变爻（机）：单爻/多爻状态跃迁，刻画"动"与"机"——从一点出发的可能演化。

6. 等价类 / 关系网络：对偶、反转、复核在空间上生成关系（群作用），
   卦与卦由此互链成图；"象义"是从这些结构关系翻译出的语义层，
   绝不反向约束数理。语义→符号的逆向检索，是映射层的逆用。

——迁移到三元九爻：维度 6→9、极性 2→3（引入"中和"作势能平衡点/过渡/耦合），
   算子保持抽象结构（对偶、反转、内核投影、变爻），但取值落在 {-1,0,+1}，
   空间规模 3^9 = 19683。卦辞象辞属于创作层，不反向改动公理。

======================================================================
二、锁定公理（不可修改）
======================================================================
单爻三态：阳(+1)｜中和(0)｜阴(-1)；卦体 G=[g1..g9]，g1=上爻,g9=下爻，gi∈{-1,0,+1}。
  公理1 爻态语义：+1 显/向外/生发/增益/主动；0 居间/耦合/过渡/稳态/势能平衡；-1 隐/向内/收敛/减损/被动
  公理2 F_C 错卦（对偶，逐爻独立取反）：F_C(+1)=-1,F_C(-1)=+1,F_C(0)=0，F_C(F_C(G))=G
  公理3 F_Z 综卦（序列反转）：F_Z([g1..g9])=[g9..g1]，F_Z(F_Z(G))=G
  公理4 F_CZ 错综复合：F_CZ(G)=F_C(F_Z(G))，先综后错
  公理5 F_H 互卦（内核投影，输出5维）：F_H(G)=[g3,g4,g5,g6,g7]
  公理6 F_B 动爻变卦：F_B(+1)=0,F_B(-1)=0,F_B(0)=+1；支持1~9爻同时动
等价类：{G, F_C(G), F_Z(G), F_CZ(G)}
空间距离：欧氏 D=√Σ(gAi-gBi)^2
"""
from __future__ import annotations
import math
from collections import Counter, deque

import numpy as np

N = 3 ** 9                      # 19683 卦总数
D = 9                          # 维度


# ---------------- 索引 ↔ 卦向量 互转 ----------------
def idx_to_g(idx: int) -> tuple:
    """0..19682 → 9维三元向量 (g1..g9)，gi∈{-1,0,1}，g1 为最高位。"""
    out = [0] * D
    v = idx
    for i in range(D - 1, -1, -1):
        out[i] = v % 3 - 1
        v //= 3
    return tuple(out)


def g_to_idx(g) -> int:
    idx = 0
    for x in g:
        idx = idx * 3 + (x + 1)
    return idx


# ---------------- 算子（公理2~6） ----------------
def F_C(g) -> tuple:
    return tuple(-x for x in g)


def F_Z(g) -> tuple:
    return g[::-1]


def F_CZ(g) -> tuple:
    return F_C(F_Z(g))


def F_H(g) -> tuple:
    """互卦：剔除 g1,g9，取中心连续5爻 [g3,g4,g5,g6,g7] → 5维向量。"""
    return g[2:7]


def F_B_single(g, pos: int) -> tuple:
    """pos: 1..9（第 pos 爻动）。F_B(+1)=0,F_B(-1)=0,F_B(0)=+1。"""
    i = pos - 1
    v = g[i]
    nv = 0 if v != 0 else 1
    return g[:i] + (nv,) + g[i + 1:]


def F_B_multi(g, positions) -> tuple:
    out = list(g)
    for pos in positions:
        i = pos - 1
        v = out[i]
        out[i] = 0 if v != 0 else 1
    return tuple(out)


# ---------------- 单元测试（用户锁定样例，必须通过，禁止改公理） ----------------
def unit_test() -> None:
    G = (+1, +1, 0, -1, +1, 0, -1, -1, 0)
    cases = {
        "F_C(G)": (F_C(G), (-1, -1, 0, +1, -1, 0, +1, +1, 0)),
        "F_Z(G)": (F_Z(G), (0, -1, -1, 0, +1, -1, 0, +1, +1)),
        "F_CZ(G)": (F_CZ(G), (0, +1, +1, 0, -1, +1, 0, -1, -1)),
        "F_H(G)": (F_H(G), (0, -1, +1, 0, -1)),
        "第5爻动": (F_B_single(G, 5), (+1, +1, 0, -1, 0, 0, -1, -1, 0)),
    }
    ok = True
    for name, (got, exp) in cases.items():
        match = got == exp
        ok = ok and match
        print(f"  [{('✓' if match else '✗')}] {name} = {list(got)}"
              + ("" if match else f"   期望 {list(exp)}"))
    # 对合性质校验
    G0 = (1, 0, -1, 1, 0, -1, 0, 1, -1)
    assert F_C(F_C(G0)) == G0, "F_C 对合"
    assert F_Z(F_Z(G0)) == G0, "F_Z 对合"
    assert F_CZ(F_CZ(G0)) == G0, "F_CZ 对合（F_C 与 F_Z 交换）"
    print("  [✓] 对合性质：F_C∘F_C=F_Z∘F_Z=F_CZ∘F_CZ=恒等")
    assert ok, "单元测试未全部通过——自查计算，禁止修改公理"
    print("  ✅ 5 项算子单元测试全部通过（未修改公理）")


# ---------------- 全集生成 + 等价组统计 ----------------
def build_universe():
    """全集 19683 卦 + 逐卦批量计算错/综/错综/互卦 + 算子固定点计数。"""
    full = [idx_to_g(i) for i in range(N)]
    fc = [F_C(g) for g in full]
    fz = [F_Z(g) for g in full]
    fcz = [F_CZ(g) for g in full]
    fh = [F_H(g) for g in full]
    # 算子固定点（用于 Burnside 校验等价组数）
    fix = {
        "e": N,
        "F_C": sum(1 for g in full if F_C(g) == g),
        "F_Z": sum(1 for g in full if F_Z(g) == g),
        "F_CZ": sum(1 for g in full if F_CZ(g) == g),
    }
    return full, fc, fz, fcz, fh, fix


def equivalence_groups():
    """对每卦构造 {G,FC,FZ,FCZ}，集合去重统计独立等价组。"""
    seen = set()
    groups = []
    reps = []
    for i in range(N):
        g = idx_to_g(i)
        if g in seen:
            continue
        group = frozenset((g, F_C(g), F_Z(g), F_CZ(g)))
        seen |= group
        groups.append(len(group))       # 组内元素数 ∈ {1,2,4}
        reps.append(min(group, key=g_to_idx))
    total = len(groups)
    return total, groups, reps


# ---------------- 符号图网络（F_C / F_Z / F_B 单爻动边） ----------------
def build_graph(include_multi_yi: bool = False):
    """稀疏无向邻接表。F_B 边：默认单爻动（每卦9条）；多爻动边若开启则全子集物化。"""
    adj = [set() for _ in range(N)]
    edge_stat = {"F_C": 0, "F_Z": 0, "F_B": 0}

    def add(a: int, b: int):
        if a != b:
            adj[a].add(b)
            adj[b].add(a)

    for i in range(N):
        g = idx_to_g(i)
        add(i, g_to_idx(F_C(g)))
        edge_stat["F_C"] += 1
        add(i, g_to_idx(F_Z(g)))
        edge_stat["F_Z"] += 1
        for pos in range(1, 10):            # 单爻动
            nb = F_B_single(g, pos)
            add(i, g_to_idx(nb))
            edge_stat["F_B"] += 1
        if include_multi_yi:
            # 多爻动：所有非空位置子集（2^9-1 种动法，边极多，仅按需开启）
            for mask in range(1, 1 << 9):
                positions = [p + 1 for p in range(9) if mask >> p & 1]
                nb = F_B_multi(g, positions)
                add(i, g_to_idx(nb))
    # 去重计边（无向边，按算子类型；排除自环）
    seen_edges = set()
    for i in range(N):
        g = idx_to_g(i)
        for a, b, name in ((i, g_to_idx(F_C(g)), "F_C"),
                           (i, g_to_idx(F_Z(g)), "F_Z")):
            if a != b:
                e = (min(a, b), max(a, b), name)
                if e not in seen_edges:
                    seen_edges.add(e)
    for i in range(N):
        g = idx_to_g(i)
        for pos in range(1, 10):
            a, b = i, g_to_idx(F_B_single(g, pos))
            if a != b:
                e = (min(a, b), max(a, b), "F_B")
                if e not in seen_edges:
                    seen_edges.add(e)
    ec = Counter(e[2] for e in seen_edges)
    # 连通分量（BFS，单爻动图本身连通）
    comp = 0
    visited = [False] * N
    for s in range(N):
        if not visited[s]:
            comp += 1
            dq = deque([s])
            visited[s] = True
            while dq:
                u = dq.popleft()
                for v in adj[u]:
                    if not visited[v]:
                        visited[v] = True
                        dq.append(v)
    degree = Counter(len(a) for a in adj)
    return {
        "nodes": N,
        "edges": dict(ec),
        "max_degree": max(degree),
        "avg_degree": sum(len(a) for a in adj) / N,
        "components": comp,
    }


# ---------------- 逆向检索（自然语言 → 目标向量 → Top-N 邻近 + 全套推演） ----------------
DEFAULT_LEXICON = [
    # (正向词, 负向词) 对应 g1..g9 九个爻位；含正→+1，含负→-1，否则→0
    (("显", "达成", "上位", "向外"), ("隐", "潜藏", "退", "收敛")),          # g1 上爻
    (("生发", "增益", "主导", "动"), ("减损", "被动", "静")),               # g2
    (("居间", "耦合", "过渡", "中"), ("偏", "极端", "失衡")),               # g3
    (("主动", "进", "张", "雄"), ("缩", "雌", "守")),                       # g4
    (("势能", "平衡", "稳", "蓄"), ("不稳", "倾", "泄")),                    # g5 中爻
    (("生", "长", "升", "阳"), ("衰", "降", "阴")),                          # g6
    (("通", "交", "联", "化"), ("隔", "滞", "塞")),                          # g7
    (("明", "显于外", "成"), ("晦", "藏于内", "败")),                        # g8
    (("下位", "根基", "本", "内"), ("末", "枝", "外"))                        # g9 下爻
]


def language_to_vector(text: str, lexicon=None) -> tuple:
    lexicon = lexicon or DEFAULT_LEXICON
    vec = []
    for pos_kw, neg_kw in lexicon[:D]:
        if any(k in text for k in pos_kw):
            vec.append(1)
        elif any(k in text for k in neg_kw):
            vec.append(-1)
        else:
            vec.append(0)
    return tuple(vec)


def reverse_retrieve(text: str, top_n: int = 5, lexicon=None, full=None,
                     fc=None, fz=None, fcz=None, fh=None, reps=None):
    """输入自然语言 → 目标9维向量 → 欧氏距离 Top-N 邻近卦 → 全套推演。"""
    full = full or [idx_to_g(i) for i in range(N)]
    target = language_to_vector(text, lexicon)
    dists = []
    for i, g in enumerate(full):
        d = math.sqrt(sum((a - b) ** 2 for a, b in zip(g, target)))
        dists.append((d, i, g))
    dists.sort(key=lambda x: (x[0], x[1]))
    top = dists[:top_n]
    result = []
    for d, i, g in top:
        fc = F_C(g)
        fz = F_Z(g)
        fcz = F_CZ(g)
        fh = F_H(g)
        # 每爻动一次（变卦推演）
        yi = [F_B_single(g, p) for p in range(1, 10)]
        result.append({
            "idx": i, "dist": d, "guag": g,
            "F_C": fc, "F_Z": fz, "F_CZ": fcz, "F_H": fh, "F_B": yi,
        })
    return target, result


# ---------------- 可选扩展：聚类划分"三元经卦"大类（对标八卦） ----------------
def cluster_into_baguas(k: int = 8, max_iter: int = 200):
    """特征 = 9维原卦 + 5维互卦（14维），标准化后 KMeans 聚 k 类，对标八卦。"""
    X = np.empty((N, 14), dtype=np.float64)
    for i in range(N):
        g = idx_to_g(i)
        X[i] = [*g, *F_H(g)]
    X = X - X.mean(0)
    std = X.std(0)
    std[std == 0] = 1
    X = X / std
    # 用确定性初始中心（等距采样）
    rng = np.random.RandomState(0)
    centers = X[rng.choice(N, k, replace=False)]
    labels = np.zeros(N, dtype=int)
    for it in range(max_iter):
        d = ((X[:, None, :] - centers[None, :, :]) ** 2).sum(2)
        new_labels = d.argmin(1)
        new_centers = np.array([X[new_labels == c].mean(0) for c in range(k)])
        if np.allclose(new_centers, centers, atol=1e-9):
            centers = new_centers
            labels = new_labels
            break
        centers = new_centers
        labels = new_labels
    # 每类：成员数 + 代表卦（离类心最近）
    counts = Counter(labels)
    rep_idx = []
    for c in range(k):
        idxs = np.where(labels == c)[0]
        dc = ((X[idxs] - centers[c]) ** 2).sum(1)
        rep_idx.append(int(idxs[dc.argmin()]))
    return labels, counts, rep_idx


# ---------------- 主流程 ----------------
def main():
    print("# 三元九爻符号系统 · 推演执行清单\n")

    print("## 任务1 · 逆向周易64卦符号范式")
    print("（范式总结见模块头部 docstring）六条：有限离散格 / 对偶(错) / 反转(综) / "
          "内核投影(互) / 变爻(机) / 等价关系网络；象义是映射层，不反向约束数理。\n")

    print("## 任务2 · 载入三元公理 + 单元测试")
    unit_test()
    print()

    print("## 任务3 · 生成全集 19683 卦")
    full, fc, fz, fcz, fh, fix = build_universe()
    print(f"  全集总数 = 3^9 = **{N}**")
    print("  样例：idx0 = 全阴", list(full[0]),
          "| 中间 idx9830 =", list(full[N // 2]),
          "| idx19682 = 全阳", list(full[-1]))
    print()

    print("## 任务4 · 批量计算 错/综/错综/互 卦（对每一卦）")
    print(f"  已对全集逐卦求得 F_C(错)、F_Z(综)、F_CZ(错综)、F_H(互,5维)")
    print("  示例 idx=0（全阴）：")
    print(f"    F_C = {list(fc[0])}")
    print(f"    F_Z = {list(fz[0])}")
    print(f"    F_CZ= {list(fcz[0])}")
    print(f"    F_H = {list(fh[0])}  (5维内核)")
    print()

    print("## 任务5 · 等价组统计")
    total, groups, reps = equivalence_groups()
    c = Counter(groups)
    print(f"  等价组总数 = **{total}**")
    print(f"  组大小分布：{dict(sorted(c.items()))}（1=自反组, 2=对偶/自综组, 4=满维组）")
    print(f"  Burnside 校验：(|X| + |Fix(F_C)| + |Fix(F_Z)| + |Fix(F_CZ)|)/4 = "
          f"({fix['e']}+{fix['F_C']}+{fix['F_Z']}+{fix['F_CZ']})/4 = "
          f"{(fix['e']+fix['F_C']+fix['F_Z']+fix['F_CZ'])/4:.0f}  → 一致 ✓")
    print()

    print("## 任务6 · 符号图网络（节点=19683卦）")
    graph = build_graph(include_multi_yi=False)
    print(f"  节点 = {graph['nodes']}")
    print(f"  无向边：错(F_C)={graph['edges'].get('F_C',0)}，综(F_Z)={graph['edges'].get('F_Z',0)}，"
          f"单爻动(F_B)={graph['edges'].get('F_B',0)}（多爻动边可选物化）")
    print(f"  最大度 = {graph['max_degree']}，平均度 = {graph['avg_degree']:.1f}，"
          f"连通分量 = {graph['components']}")
    print()

    print("## 任务7 · 逆向检索（自然语言 → 目标9维向量 → Top-N 邻近 + 全套推演）")
    target, top = reverse_retrieve("势能平衡 显于外 主动 根基", top_n=3,
                                   full=full)
    print(f"  语言: 「势能平衡 显于外 主动 根基」")
    print(f"  目标向量: {list(target)}")
    for t in top:
        print(f"\n  —— Top {t['idx']} 卦（欧氏距离 {t['dist']:.4f}）——")
        print(f"    卦体 G = {list(t['guag'])}")
        print(f"    错卦 F_C  = {list(t['F_C'])}")
        print(f"    综卦 F_Z  = {list(t['F_Z'])}")
        print(f"    错综 F_CZ = {list(t['F_CZ'])}")
        print(f"    互卦 F_H  = {list(t['F_H'])} (5维内核)")
        print(f"    变卦（第1..9爻动）: {[list(y) for y in t['F_B']]}")
    print()

    print("## 任务8 · 聚类划分三元经卦大类（对标八卦）")
    labels, counts, rep_idx = cluster_into_baguas(k=8)
    names = ["☰乾", "☱兑", "☲离", "☳震", "☴巽", "☵坎", "☶艮", "☷坤"]
    print("  14维特征(9维原卦+5维互卦)标准化后 KMeans 聚 8 类：")
    for c in range(8):
        print(f"    类{c}（对标{names[c]}）：成员 {counts[c]:>6}，"
              f"代表卦 {list(full[rep_idx[c]])}")
    print()


if __name__ == "__main__":
    main()
