# -*- coding: utf-8 -*-
"""卦典·人类语言转译引擎。

母结构（三元九爻 D/R/T）→ 人类原有认知语言（周易传统卦辞 + 通俗释义 + 生活启示）。
原则：结构归母（D/R/T 三元不动），表达归人类。确定性、可复现：同一卦永远产出同一卦辞。

确定性转译表（位 × 态）：
  爻位 g1..g9 = 上势/上承/上纳 · 中转/中衡/中通 · 下启/下固/下基
  爻态 D(承载·削减·封存)→藏收固止 | R(审定·评估·回灌)→察度辨审 | T(增益·势能·递送)→发行通扬
"""
import csv
import json
import os

_H = os.path.dirname(os.path.abspath(__file__))
OUT_CSV = os.path.join(_H, "sanjiu_quanji_human.csv")
OUT_JSON = os.path.join(_H, "sanjiu_quanji_human.json")

DRT2I = {"D": 0, "R": 1, "T": 2}

# 位 × 态 → 文言词（9 位 g1..g9，按 上→下 排；D/R/T）
WENYAN = {
    0: ["止", "度", "扬"], 1: ["藏", "审", "行"], 2: ["敛", "辨", "纳"],
    3: ["守", "转", "动"], 4: ["静", "中", "明"], 5: ["滞", "导", "通"],
    6: ["闭", "察", "启"], 7: ["蓄", "度", "生"], 8: ["沉", "观", "发"],
}
# 位 × 态 → 通俗词
SU = {
    0: ["收束", "权衡", "外扬"], 1: ["隐藏", "审度", "前行"], 2: ["敛聚", "明辨", "接纳"],
    3: ["固守", "转圜", "发动"], 4: ["沉静", "中正", "昭明"], 5: ["阻滞", "疏导", "通达"],
    6: ["闭藏", "觉察", "开启"], 7: ["蓄积", "估量", "生发"], 8: ["沉潜", "观察", "萌发"],
}
# 三层（上/中/下 对应的 g 下标 0..8；g1=上爻=0，g9=下爻=8）
LAYERS = {"下": (6, 7, 8), "中": (3, 4, 5), "上": (0, 1, 2)}
LNAME = {"下": "基", "中": "枢", "上": "势"}


def _idx(drt):
    n = 0
    for c in drt:
        n = n * 3 + DRT2I[c]
    return n


def _counts(drt):
    return drt.count("D"), drt.count("R"), drt.count("T")


def layer_verdict(ds):
    """某层三爻 → 层断辞（文言）。ds: 该层 3 个 D/R/T 字符（自下而上或按层序均可）。"""
    d, r, t = ds.count("D"), ds.count("R"), ds.count("T")
    if d == 3:
        return "重阴厚藏，宜静宜守"
    if r == 3:
        return "三衡相济，审于中正"
    if t == 3:
        return "纯阳通泰，动而宜行"
    if t == 2 and d == 1:
        return "阳动阴承，行而有节"
    if d == 2 and t == 1:
        return "阴厚阳微，守而后动"
    if r == 2:
        return "衡众居中，审时待机"
    return "阴阳参差，动静相济"


def break_verdict(drt):
    """总断辞（吉凶悔吝倾向，由全局 D/R/T 分布确定性得出）。"""
    d, r, t = _counts(drt)
    if t >= 6:
        return "元亨，利有攸往，吉", "阳动盛大，宜乘势而为，主动进取", "乘势而行，主动作为之时"
    if d >= 6:
        return "利贞，宜守宜藏，静待时势", "阴重收敛，宜蓄不宜发，静以守成", "养晦蓄势，静待天时"
    if r >= 6:
        return "贞吉，慎辨明度，无咎", "审度居中，谋定后动，可免悔吝", "谋定后动，审时度势"
    if t > d and t > r:
        return "亨，小吉，利行而不宜躁", "阳势为主，可行而忌急进", "顺势而行，戒骄戒躁"
    if d > t and d > r:
        return "贞，小吝，宜蓄不宜发", "阴势为主，宜收宜藏，静以蓄力", "收敛固本，静观其变"
    if r > t and r > d:
        return "悔亡，审时而后动", "衡主其中，宜辨宜度，待机而动", "审时度势，谋定后动"
    return "无咎，中和守正", "阴阳中和，动静相济，守正无咎", "守中持衡，不偏不倚"


def humanize(drt):
    """drt: 9 字符 D/R/T（g1 上→g9 下）。返回人类语言卦辞 dict。"""
    # 三层：文言/通俗/层断
    gw, gs, gv = {}, {}, {}
    for name, pos in LAYERS.items():
        chars = [drt[p] for p in pos]
        gw[name] = "".join(WENYAN[p][DRT2I[drt[p]]] for p in pos)
        gs[name] = "、".join(SU[p][DRT2I[drt[p]]] for p in pos)
        gv[name] = layer_verdict(chars)
    bd, bd_s, bd_q = break_verdict(drt)
    yin = yinyang(drt)
    # 人类卦名：阴阳 + 断辞主词 + 三层首字
    ming = f"{yin}·{bd.split('，')[0]}·{gw['下'][0]}{gw['中'][0]}{gw['上'][0]}卦"
    # 传统卦辞（文言，自下而上：下→中→上）
    guan = (f"下卦{''.join(WENYAN[p][DRT2I[drt[p]]] for p in reversed(LAYERS['下']))}，其基{gv['下']}；"
            f"中卦{''.join(WENYAN[p][DRT2I[drt[p]]] for p in LAYERS['中'])}，其枢{gv['中']}；"
            f"上卦{''.join(WENYAN[p][DRT2I[drt[p]]] for p in reversed(LAYERS['上']))}，其势{gv['上']}。"
            f"{bd}。")
    # 通俗释义
    su = (f"此卦下盘{'、'.join(SU[p][DRT2I[drt[p]]] for p in LAYERS['下'])}，{gv['下']}；"
          f"中道{'、'.join(SU[p][DRT2I[drt[p]]] for p in LAYERS['中'])}，{gv['中']}；"
          f"上势{'、'.join(SU[p][DRT2I[drt[p]]] for p in LAYERS['上'])}，{gv['上']}。{bd_s}。")
    return {
        "idx": _idx(drt), "drt": drt, "yinyang": yin,
        "ming": ming, "guan": guan, "su": su, "qi": bd_q,
    }


def yinyang(drt):
    d, r, t = _counts(drt)
    return "阳" if t > d else "阴" if d > t else "中"


def gen_all():
    out = {}
    for n in range(19683):
        x, d = n, ""
        for _ in range(9):
            d = "DRT"[x % 3] + d
            x //= 3
        out[n] = humanize(d)
    return out


if __name__ == "__main__":
    d = gen_all()
    print("全量卦数:", len(d))
    for n in [0, 19682, 189]:
        h = d[n]
        print(f"--- idx {n} ({h['drt']}) {h['yinyang']} ---")
        print("  卦名:", h["ming"])
        print("  传统:", h["guan"])
        print("  通俗:", h["su"])
        print("  启示:", h["qi"])
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=0)
    with open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["idx", "drt", "yinyang", "ming", "guan", "su", "qi"])
        for n in range(19683):
            h = d[n]
            w.writerow([h["idx"], h["drt"], h["yinyang"], h["ming"], h["guan"], h["su"], h["qi"]])
    print("写出:", OUT_CSV, os.path.getsize(OUT_CSV), "B ;", OUT_JSON, os.path.getsize(OUT_JSON), "B")
