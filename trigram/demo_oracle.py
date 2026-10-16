# -*- coding: utf-8 -*-
"""以言入卦 · 象义闭环演示：多条自然语言入卦，命中等价组并得卦辞解说。
同时导出全集卦辞集（5002 等价组）。
"""
from oracle import retrieve_with_oracle, dump_oracle_csv

QUERIES = [
    "躬身而行，躬身入局",
    "主动进取 显明于外 根基稳固",
    "重阴覆顶 位高失据 收敛下行",
    "执枢得中 通达交感",
    "居尊得位 刚健有为 生发上升",
]

for q in QUERIES:
    target, hits = retrieve_with_oracle(q, top_n=2)
    print(f"【{q}】→ 目标向量 {list(target)}")
    for h in hits:
        print(f"  命中 idx{h['idx']}(组{h['group_rep_idx']}) 距{h['dist']:.3f} 卦{h['hexagram']}")
        print(f"    象义  「{h['oracle']['name']}」{h['oracle']['statement']}")
    print()

print("导出全集卦辞集 CSV ...")
n = dump_oracle_csv("oracle_full.csv")
print(f"  已导出 {n} 个等价组的卦辞 → oracle_full.csv\n")

print("== 变爻断辞（以「躬身而行，躬身入局」命中的太和卦为例） ==")
_, hits = retrieve_with_oracle("躬身而行，躬身入局", top_n=1)
h = hits[0]
print(f"  卦「{h['oracle']['name']}」{h['oracle']['statement']}")
for y in h["yi"]:
    print("   ", y["statement"])
