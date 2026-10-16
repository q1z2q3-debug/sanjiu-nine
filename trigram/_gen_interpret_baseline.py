# -*- coding: utf-8 -*-
"""批量生成 19683 卦的"解读坐标系基线"。

解读坐标系：从 9 维卦确定性映射到 9 个诗评维度判定（主旨显隐/情感强度/意象虚实/
用典深浅/音律平仄/修辞张力/意脉通滞/境界显晦/立意根基），作为每首解读的出处基座。
本基线全量、可复现、可审计：同一卦永远得到同一坐标。"""
import csv, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from interpret import coordinate, AXIS

def trits_to_idx(g):
    n = 0
    for v in g:
        n = n * 3 + (v + 1)  # -1->0, 0->1, 1->2
    return n

def main():
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "interpret_coords.csv")
    rows = []
    for n in range(19683):
        # 三进制解码成 9 维卦（-1/0/+1）
        x = n
        g = [0] * 9
        for i in range(8, -1, -1):
            g[i] = (x % 3) - 1
            x //= 3
        c = coordinate(g)
        rows.append([n] + g + [c[a] for a in AXIS])
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["idx", "g1", "g2", "g3", "g4", "g5", "g6", "g7", "g8", "g9"] + AXIS)
        w.writerows(rows)
    # 验证
    assert len(rows) == 19683, f"行数={len(rows)} != 19683"
    assert len({r[0] for r in rows}) == 19683, "idx 重复"
    print(f"已生成 19683 卦坐标基线: {out}")
    print(f"行数 = {len(rows)}，idx 唯一 = {len({r[0] for r in rows})}")
    # 抽样：全中和卦与样例卦
    zero = [r for r in rows if r[1:10] == [0]*9][0]
    print("全中和卦 [0]*9:", {a: c for a, c in zip(AXIS, zero[10:])})
    sample = [r for r in rows if r[1:10] == [1,1,1,-1,0,1,1,1,1]][0]
    print("样例卦(纸鸢) 坐标:", {a: c for a, c in zip(AXIS, sample[10:])})

if __name__ == "__main__":
    main()
