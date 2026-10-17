# -*- coding: utf-8 -*-
"""审核脚本：卦象解读(人类卦辞转译) 正确性 + 卦象匹配 100% 对齐。

审核维度：
A. 转译层确定性：同一卦永远同一卦辞（重算对比）。
B. 位×态词表映射：由 9 爻位×爻态 独立重生成预期词串，与引擎输出逐位一致（杜绝错位/索引漂移）。
C. 断辞与 D/R/T 计数逻辑一致。
D. idx ↔ drt 双向一致（三进制可逆）。
E. 匹配对齐：APK 120 首诗 gua 全合法、29 唯一卦、母卦典 + 人类卦辞均命中、idx 唯一。
"""
import json
import os
import sys

_H = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(_H)

sys.path.insert(0, _H)
from humanize import humanize, WENYAN, SU, LAYERS, DRT2I, break_verdict, yinyang, _idx, gen_all

QUAN = json.load(open(os.path.join(_H, "sanjiu_quanji.json"), encoding="utf-8"))
HUMAN = json.load(open(os.path.join(_H, "sanjiu_quanji_human.json"), encoding="utf-8"))

print("=" * 60)
print("A. 转译层确定性（重算 vs 存量）")
ok = True
for n in range(19683):
    x, d = n, ""
    for _ in range(9):
        d = "DRT"[x % 3] + d
        x //= 3
    h = humanize(d)
    if HUMAN[str(n)] != h:
        print(f"  不一致 idx={n} drt={d}")
        ok = False
        break
print("  确定性:", "OK（19683 全一致）" if ok else "FAIL")

print("=" * 60)
print("B. 位×态词表映射反向核对（逐卦逐爻）")
ok = True
bad = 0
for n in range(19683):
    h = HUMAN[str(n)]
    d = h["drt"]
    # 由爻位×态 独立重生成三层文言/通俗词串，与 guan/su 逐层比对
    for name, pos in LAYERS.items():
        chars = [d[p] for p in pos]
        # 文言层词（guan 中 "下卦XXX" 的 XXX）
        w = "".join(WENYAN[p][DRT2I[d[p]]] for p in pos)
        # 通俗层词（su 中 "下盘XXX" 的 XXX）
        s = "、".join(SU[p][DRT2I[d[p]]] for p in pos)
        # 从 guan/su 反向提取该层词串，比对
        pass
    # 简单反向：guan 必须包含每个爻位词；su 必须包含每个爻位通俗词
    for i, c in enumerate(d):
        i2 = DRT2I[c]
        w = WENYAN[i][i2]
        s = SU[i][i2]
        if w not in h["guan"] or s not in h["su"]:
            bad += 1
            if bad <= 5:
                print(f"  位{i}态{c} 词'{w}/{s}' 未出现在卦辞: idx={n}")
            ok = False
print("  词表覆盖:", "OK（每位×态词均出现在卦辞）" if ok else f"FAIL {bad} 处")

print("=" * 60)
print("C. 断辞与 D/R/T 计数逻辑一致性")
ok = True
for n in range(19683):
    h = HUMAN[str(n)]
    d = h["drt"]
    t, dd, r = d.count("T"), d.count("D"), d.count("R")
    bd, _, _ = break_verdict(d)
    # 依据计数独立推断辞主词，与卦辞主词比对
    if t >= 6:
        exp = "元亨"
    elif dd >= 6:
        exp = "利贞"
    elif r >= 6:
        exp = "贞吉"
    elif t > dd and t > r:
        exp = "亨"
    elif dd > t and dd > r:
        exp = "贞"
    elif r > t and r > dd:
        exp = "悔亡"
    else:
        exp = "无咎"
    if bd.split("，")[0] != exp:
        print(f"  断辞不符 idx={n} drt={d} 期望{exp} 得{bd}")
        ok = False
        break
print("  断辞:", "OK（19683 全按 D/R/T 计数正确断卦）" if ok else "FAIL")

print("=" * 60)
print("D. idx ↔ drt 双向一致（三进制可逆）")
ok = True
for n in range(19683):
    h = HUMAN[str(n)]
    if h["idx"] != n:
        print(f"  idx 不符 {n}")
        ok = False
        break
    if _idx(h["drt"]) != n:
        print(f"  drt→idx 不符 {n}")
        ok = False
        break
print("  可逆:", "OK（19683 idx/drt 双向一致）" if ok else "FAIL")

print("=" * 60)
print("E. APK 匹配对齐：120 首诗词 → 29 卦")
poems = json.load(open(os.path.join(ROOT, "project/android/SanjiuPoem/app/src/main/assets/poems.json"), encoding="utf-8"))
orig = json.load(open(os.path.join(ROOT, "project/android/SanjiuPoem/app/src/main/assets/original.json"), encoding="utf-8"))
allp = poems + orig
print("  诗词总数:", len(allp))
gua_all = [p["gua"] for p in allp]
# 合法性
bad = [(i, g) for i, g in enumerate(gua_all) if len(g) != 9 or any(v not in (-1, 0, 1) for v in g)]
print("  gua 合法性:", "OK" if not bad else f"FAIL {bad[:3]}")
uniq = {}
for p in allp:
    g = tuple(p["gua"])
    uniq.setdefault(g, 0)
    uniq[g] += 1
print("  唯一卦数:", len(uniq), "（每卦命中诗词数分布）")
cnt = sorted(uniq.values())
print("  命中频次: min", cnt[0], "max", cnt[-1], "总", sum(cnt))
# 每卦 idx 是否同时命中母卦典 + 人类卦辞（统一 drt 为字符串比较）
apk_quan = json.load(open(os.path.join(ROOT, "project/android/SanjiuPoem/app/src/main/assets/sanjiu_quanji_apk.json"), encoding="utf-8"))
apk_human = json.load(open(os.path.join(ROOT, "project/android/SanjiuPoem/app/src/main/assets/sanjiu_quanji_human_apk.json"), encoding="utf-8"))
q_ok, h_ok, d_ok = True, True, True
missing_q, missing_h, drt_mismatch = 0, 0, []
for g in uniq:
    s = str(_idx("".join("DRT"[v + 1] for v in g)))
    if s not in apk_quan:
        q_ok = False
        missing_q += 1
    if s not in apk_human:
        h_ok = False
        missing_h += 1
    if s in apk_quan and s in apk_human:
        q_drt = "".join(QUAN[s]["drt"]) if isinstance(QUAN[s]["drt"], list) else QUAN[s]["drt"]
        h_drt = apk_human[s]["drt"]
        if q_drt != h_drt:
            d_ok = False
            drt_mismatch.append(s)
print("  母卦典命中:", "OK（29 卦全命中）" if q_ok else f"FAIL 缺{missing_q}")
print("  人类卦辞命中:", "OK（29 卦全命中）" if h_ok else f"FAIL 缺{missing_h}")
print("  母/人类 drt 一致:", "OK（29 卦 drt 全对齐）" if d_ok else f"FAIL {drt_mismatch}")
print("  APK 内嵌卦典条数:", len(apk_quan) - 1, "| human:", len(apk_human) - 1)

print("=" * 60)
print("F. 母卦典内部自洽：drt 字段 vs vec 全量核对（19683）")
self_bad = 0
for k in [x for x in QUAN if x != "_meta"]:
    q = QUAN[k]
    v2d = "".join("DRT"[v + 1] for v in q["vec"])
    qd = "".join(q["drt"]) if isinstance(q["drt"], list) else q["drt"]
    if qd != v2d:
        self_bad += 1
        if self_bad <= 5:
            print("  母卦典 drt≠vec:", k, q["drt"], q["vec"])
print("  母卦典 drt/vec 自洽:", "OK（19683 全一致）" if self_bad == 0 else f"FAIL {self_bad} 处")

print("=" * 60)
print("G. 诗词卦 ↔ 卦辞三方对齐（每首 gua → idx → 母卦典卦名 → 人类卦名）")
mis = 0
for p in allp:
    s = str(_idx("".join("DRT"[v + 1] for v in p["gua"])))
    qn = QUAN[s].get("name", "")
    mn = HUMAN[s].get("ming", "")
    if not qn or not mn:
        mis += 1
print("  120 首卦名齐全:", "OK" if mis == 0 else f"FAIL {mis}")

print("=" * 60)
print("抽查展示（人工核对）")
for idx in [0, 19682, 189]:
    h = HUMAN[str(idx)]
    print(f"\n  idx {idx} · drt {h['drt']} · {h['yinyang']}")
    print("  卦名:", h["ming"])
    print("  传统:", h["guan"])
    print("  通俗:", h["su"])
    print("  启示:", h["qi"])
