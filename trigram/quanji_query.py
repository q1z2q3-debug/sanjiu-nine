# -*- coding: utf-8 -*-
"""深度卦典查询模块：按卦向量/idx 取 19683 卦的深度卦辞（总释/分层/制衡/自适配/演化）。

数据源 trigram/sanjiu_quanji.json（19683 卦，其中 19656 卦有人工卦辞，
(01上,08中) 27 卦因源文档错配缺失，标记 has_text=False 并给出体系补注 sys_note）。
"""
import json
import os

_Q = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sanjiu_quanji.json")
_LIGHT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sanjiu_quanji_light.csv")
_GUAS = None


def load():
    global _GUAS
    if _GUAS is None:
        _GUAS = json.load(open(_Q, encoding="utf-8"))
    return _GUAS


def idx_of(vec):
    """9 维向量（元素 ∈ {-1,0,1}）→ 19683 卦唯一索引 0..19682。"""
    n = 0
    for v in vec:
        n = n * 3 + (v + 1)
    return n


def gua(vec):
    """按卦向量取卦信息（含卦名/卦辞/has_text/sys_note）。"""
    d = load()
    return d[str(idx_of(vec))]


def gua_by_idx(idx):
    """按 idx 取卦信息。"""
    return load()[str(idx)]


def search(vec, top_n=5, key="zongshi"):
    """按卦向量检索并返回 Top-N 深度卦辞摘要（供逆向检索语义→卦→卦辞）。"""
    d = load()
    r = d[str(idx_of(vec))]
    return {k: r.get(k, "") for k in ("idx", "U", "Uname", "M", "Mname", "B", "Bname",
                                      "name", "drt", "vec", "has_text", "sys_note")}


if __name__ == "__main__":
    # 自检：全中和卦 与 缺失卦
    d = load()
    print("卦典卦数:", len(d))
    miss = [i for i, r in d.items() if not r["has_text"]]
    print("缺失卦(has_text=False):", len(miss), "示例 idx:", miss[0] if miss else None)
    r = gua([-1, -1, -1, -1, -1, -1, -1, -1, -1])  # 全 D（厚藏）
    print("全阴卦:", r["name"], "| 卦辞覆盖:", bool(r.get("zongshi")))
