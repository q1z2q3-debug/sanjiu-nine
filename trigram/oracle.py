# -*- coding: utf-8 -*-
"""象义引擎（三元九爻 · 映射层创作）。

公理锁定数理，本模块只在"象义"这一映射层上创作：为每一个等价组生成
可言的卦辞象辞。它不触碰、不修改任何算子与公理，只把结构读成语言。

生成逻辑：
  1) 爻位意象：9 爻位各配 阳/阴 意象词（中和爻=居间持中，不逐爻写）。
  2) 体势：由阳/阴爻数定"阳实外发 / 阴凝内敛 / 阴阳相济"。
  3) 机：由互卦内核（5维）极性偏斜定"内核向显/向隐/持平"，给出机宜。
  4) 全中和卦（太和）专属象辞。
"""
from __future__ import annotations

import trigram as T

# 爻位意象（9 爻位 × 阳/阴），中和爻统一为"居间持中"不重复列
ORACLE_WORD = {
    1: {"+1": "天光外发", "-1": "重阴覆顶"},
    2: {"+1": "居尊得位", "-1": "位高失据"},
    3: {"+1": "刚健有为", "-1": "刚愎自用"},
    4: {"+1": "主动进取", "-1": "退守敛藏"},
    5: {"+1": "执枢得中", "-1": "失衡偏倾"},
    6: {"+1": "生发上升", "-1": "收敛下行"},
    7: {"+1": "通达交感", "-1": "滞涩隔绝"},
    8: {"+1": "显明于外", "-1": "晦藏于内"},
    9: {"+1": "根基稳固", "-1": "根基虚浮"},
}
# 爻位名象单字（阳/阴），用于组名助记；中和=中
NAME_CHAR = {
    1: {"+1": "亢", "-1": "潜", "0": "虚"},
    2: {"+1": "尊", "-1": "孤", "0": "泰"},
    3: {"+1": "健", "-1": "戾", "0": "持"},
    4: {"+1": "进", "-1": "守", "0": "随"},
    5: {"+1": "中", "-1": "偏", "0": "枢"},
    6: {"+1": "升", "-1": "降", "0": "平"},
    7: {"+1": "通", "-1": "塞", "0": "连"},
    8: {"+1": "明", "-1": "晦", "0": "潜"},
    9: {"+1": "固", "-1": "浮", "0": "静"},
}
TAIHE = "太和"


def body(g) -> str:
    np_ = sum(1 for x in g if x == 1)
    nm = sum(1 for x in g if x == -1)
    if np_ > nm:
        return "阳实外发"
    if nm > np_:
        return "阴凝内敛"
    return "阴阳相济"


def inner_ji(g) -> str:
    h = T.F_H(g)
    hp = sum(1 for x in h if x == 1)
    hn = sum(1 for x in h if x == -1)
    if hp > hn:
        return "内核向显，机在进取"
    if hn > hp:
        return "内核向隐，机在收敛"
    return "内核持平，机在相济"


def oracle(g):
    """为单卦 g 生成象义。g: 9维三元 tuple。"""
    if all(x == 0 for x in g):
        return {
            "name": TAIHE,
            "hexagram": list(g),
            "statement": "太和之象：九爻持中，阴阳相济，势能平衡；守中待机，静极而动。",
        }
    yao = [ORACLE_WORD[i + 1][{1: "+1", -1: "-1"}[x]]
           for i, x in enumerate(g) if x != 0]
    n0 = sum(1 for x in g if x == 0)
    CN = "一二三四五六七八九"
    if n0 > 0:
        yao.append("中爻" if n0 == 1 else f"{CN[n0-1]}爻居间待机")
    yao_s = "、".join(yao)
    # 组名助记：体势 + 第一个非中和爻位的名象字
    first = next((i for i, x in enumerate(g) if x != 0), None)
    char = NAME_CHAR[first + 1][{1: "+1", -1: "-1"}[g[first]]] if first is not None else ""
    name = f"{body(g)}·{char}"
    return {
        "name": name,
        "hexagram": list(g),
        "statement": f"{body(g)}之象：{yao_s}。{inner_ji(g)}。",
    }


# ---------------- 卦 → 等价组代表卦 ----------------
_REP_CACHE = {}


def representative_idx(idx: int) -> int:
    """idx 所属等价组的代表卦 idx（组内按 g_to_idx 最小者）。"""
    if idx in _REP_CACHE:
        return _REP_CACHE[idx]
    g = T.idx_to_g(idx)
    rep = min((g, T.F_C(g), T.F_Z(g), T.F_CZ(g)), key=T.g_to_idx)
    ridx = T.g_to_idx(rep)
    # 缓存整组，加速批量
    for member in (g, T.F_C(g), T.F_Z(g), T.F_CZ(g)):
        _REP_CACHE[T.g_to_idx(member)] = ridx
    return ridx


def group_oracle(idx: int) -> dict:
    """idx 所属等价组的象义（以代表卦为名）。"""
    return oracle(T.idx_to_g(representative_idx(idx)))


# ---------------- 变爻断辞（把"动"翻译成话） ----------------
# 爻位阶段（pos1=上爻 … pos9=初爻）：位置贵贱 → 断语偏向
STAGE = {1: "上爻·极", 2: "五爻·尊", 3: "四爻·用",
         4: "三爻·守", 5: "中爻·枢", 6: "六爻·升",
         7: "七爻·进", 8: "八爻·蓄", 9: "初爻·基"}
GUI_POS = (2, 3, 4, 5)          # 当位而动 → 吉
XIAN_POS = (1, 9)               # 临极/初基 → 慎
CN_NUM = "一二三四五六七八九"


def _body_shift(g, ng) -> str:
    """变后势向：阳/阴/中和爻数变化 → 一句势语。"""
    dn = sum(1 for x in ng if x == 1) - sum(1 for x in g if x == 1)
    dc = sum(1 for x in ng if x == -1) - sum(1 for x in g if x == -1)
    d0 = sum(1 for x in ng if x == 0) - sum(1 for x in g if x == 0)
    if dn > 0:
        return "变而阳势外发"
    if dc > 0:
        return "变而阴势内敛"
    if d0 > 0:
        return "变而转趋持中"
    return "变而势不变"


def yi_divination(g):
    """对单卦 g 的第 1..9 爻各动一次，配一句断辞。输出 9 句。"""
    out = []
    for pos in range(1, 10):
        v = g[pos - 1]
        ng = T.F_B_single(g, pos)
        if v == 0:
            dir_s, verdict = "由中和而发，静极生动", "发动"
            if pos in GUI_POS:
                verdict = "当位发动，吉"
            elif pos in XIAN_POS:
                verdict = "临极而发，慎"
        elif v == 1:
            dir_s = "由阳回蓄，动极归静"
            verdict = "收敛回蓄，宜守"
        else:
            dir_s = "由阴转平，藏而化通"
            verdict = "平复化解，安"
        out.append({
            "pos": pos, "stage": STAGE[pos],
            "statement": (f"动{CN_NUM[pos-1]}爻·{STAGE[pos]}：{dir_s}；{verdict}。"
                          f"{_body_shift(g, ng)}。变卦 {list(ng)}"),
            "changed_to": ng,
        })
    return out


# ---------------- 检索 + 象义闭环 ----------------
def retrieve_with_oracle(text: str, top_n: int = 3, lexicon=None):
    """自然语言 → 目标向量 → Top-N 邻近卦 → 每卦附带 错/综/错综/互/变 + 象义解说。

    解说按**命中卦本身**生成（错卦是相反之象，若按组代表卦会讲反）；
    所属等价组代表 idx 一并标注，供归档定位。
    """
    target, top = T.reverse_retrieve(text, top_n=top_n, lexicon=lexicon)
    out = []
    for t in top:
        out.append({
            "idx": t["idx"], "dist": t["dist"],
            "hexagram": t["guag"],
            "F_C": t["F_C"], "F_Z": t["F_Z"], "F_CZ": t["F_CZ"],
            "F_H": t["F_H"], "F_B": t["F_B"],
            "group_rep_idx": representative_idx(t["idx"]),
            "oracle": oracle(t["guag"]),
            "yi": yi_divination(t["guag"]),
        })
    return target, out


# ---------------- 全集卦辞集导出 ----------------
def dump_oracle_csv(path: str):
    """把 5002 个等价组（以代表卦为名）的象义导出为 CSV。"""
    import csv
    reps = set()
    for i in range(T.N):
        reps.add(representative_idx(i))
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["组代表卦idx", "卦体9维", "卦名", "象辞"])
        for ridx in sorted(reps):
            o = oracle(T.idx_to_g(ridx))
            w.writerow([ridx, "".join(str(x) for x in o["hexagram"]),
                        o["name"], o["statement"]])
    return len(reps)


if __name__ == "__main__":
    target, hits = retrieve_with_oracle("躬身而行，躬身入局", top_n=3)
    print("目标向量:", list(target))
    for h in hits:
        print(f"\n  idx {h['idx']}（组代表 {h['group_rep_idx']}）距离 {h['dist']:.3f}")
        print("    卦体", h["hexagram"])
        print("    象义：", h["oracle"]["name"], "｜", h["oracle"]["statement"])
