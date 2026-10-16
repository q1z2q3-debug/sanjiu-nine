# -*- coding: utf-8 -*-
"""为缺失卦生成体系补注 + 产出轻量卦典 CSV（无长文本，供快速检索与入库）。"""
import csv
import json
import os
import sys

_H = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _H)
from interpret import coordinate  # noqa: E402

JP = os.path.join(_H, "sanjiu_quanji.json")
LP = os.path.join(_H, "sanjiu_quanji_light.csv")


def main():
    d = json.load(open(JP, encoding="utf-8"))
    n_sys = 0
    for i, r in d.items():
        if not r["has_text"]:
            co = coordinate(r["vec"])
            co_txt = "，".join(f"{k}·{v}" for k, v in co.items())
            r["sys_note"] = ("[体系补注] 该卦源文档(01上08中)错配缺失，无人工卦辞；"
                             f"以下为体系解读坐标补注：{co_txt}。")
            if not r["name"]:
                r["name"] = f"{r['Uname']}{r['Mname']}{r['Bname']}卦（体系补注）"
            n_sys += 1
    json.dump(d, open(JP, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    # 轻量 CSV
    with open(LP, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["idx", "U", "Uname", "M", "Mname", "B", "Bname", "name",
                    "d1","d2","d3","d4","d5","d6","d7","d8","d9",
                    "v1","v2","v3","v4","v5","v6","v7","v8","v9", "has_text"])
        for i in sorted(d, key=lambda x: int(x)):
            r = d[i]
            w.writerow([i, r["U"], r["Uname"], r["M"], r["Mname"], r["B"], r["Bname"],
                        r["name"]] + r["drt"] + r["vec"] + [r["has_text"]])
    print(f"补齐体系注: {n_sys} 卦")
    print(f"轻量卦典: {LP}（{os.path.getsize(LP)} B）")
    # 抽查补注
    for i in sorted(d, key=lambda x: int(x)):
        if not d[i]["has_text"]:
            print("  补注示例 idx=", i, d[i]["name"], "->", d[i]["sys_note"][:60])
            break


if __name__ == "__main__":
    main()
