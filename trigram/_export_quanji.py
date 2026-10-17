# -*- coding: utf-8 -*-
"""从 sanjiu_quanji.json 重新导出完整 CSV 与轻量 CSV（含补齐后的 19683 卦）。"""
import csv
import json
import os

_H = os.path.dirname(os.path.abspath(__file__))
JP = os.path.join(_H, "sanjiu_quanji.json")
CSV = os.path.join(_H, "sanjiu_quanji.csv")
LIGHT = os.path.join(_H, "sanjiu_quanji_light.csv")


def main():
    d = json.load(open(JP, encoding="utf-8"))
    idxs = sorted(d, key=lambda x: int(x))
    # 完整 CSV
    with open(CSV, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["idx", "U", "Uname", "M", "Mname", "B", "Bname", "name",
                    "d1","d2","d3","d4","d5","d6","d7","d8","d9",
                    "v1","v2","v3","v4","v5","v6","v7","v8","v9",
                    "zongshi", "fenceng", "zhiheng", "zishiying", "yanhua", "has_text"])
        for i in idxs:
            r = d[i]
            w.writerow([i, r["U"], r["Uname"], r["M"], r["Mname"], r["B"], r["Bname"],
                        r["name"]] + r["drt"] + r["vec"] +
                       [r["zongshi"], r["fenceng"], r["zhiheng"],
                        r["zishiying"], r["yanhua"], r["has_text"]])
    # 轻量 CSV
    with open(LIGHT, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["idx", "U", "Uname", "M", "Mname", "B", "Bname", "name",
                    "d1","d2","d3","d4","d5","d6","d7","d8","d9",
                    "v1","v2","v3","v4","v5","v6","v7","v8","v9", "has_text"])
        for i in idxs:
            r = d[i]
            w.writerow([i, r["U"], r["Uname"], r["M"], r["Mname"], r["B"], r["Bname"],
                        r["name"]] + r["drt"] + r["vec"] + [r["has_text"]])
    miss = [i for i, r in d.items() if not r["has_text"]]
    print(f"导出卦数: {len(d)}，has_text 缺失: {len(miss)}")
    print(f"完整 CSV: {CSV} ({os.path.getsize(CSV)//1024//1024} MB)")
    print(f"轻量 CSV: {LIGHT} ({os.path.getsize(LIGHT)//1024//1024} MB)")


if __name__ == "__main__":
    main()
