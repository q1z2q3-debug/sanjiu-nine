# -*- coding: utf-8 -*-
"""演示：大模型直接接入的语义解码 → 逆向检索 → 象义 → 变爻断辞。

通道说明：环境未配置 LLM_API_KEY 时，`try_real_llm` 返回 None，
走"主模型注入"通道——由对话中的大模型（Doubao 本身）当场语义解码，
这就是"大模型直接接入"：接入的就是我自身，而非关键词表。
"""
from llm_decoder import try_real_llm, inject_vector
from oracle import retrieve_with_oracle, oracle, representative_idx, yi_divination
import trigram as T
import math


def retrieve_with_oracle_from(text, vector, top_n=3):
    """用给定目标向量直接检索（绕开关键词表解码）。"""
    full = [T.idx_to_g(i) for i in range(T.N)]
    dists = sorted(
        ((math.sqrt(sum((a - b) ** 2 for a, b in zip(g, vector))), i, g)
         for i, g in enumerate(full)),
        key=lambda x: (x[0], x[1]))[:top_n]
    out = []
    for d, i, g in dists:
        out.append({
            "idx": i, "dist": d, "hexagram": g,
            "F_C": T.F_C(g), "F_Z": T.F_Z(g), "F_CZ": T.F_CZ(g),
            "F_H": T.F_H(g), "F_B": [T.F_B_single(g, p) for p in range(1, 10)],
            "group_rep_idx": representative_idx(i),
            "oracle": oracle(g), "yi": yi_divination(g),
        })
    return out


# 一句关键词表覆盖不了的口语
TEXT = "项目胎死腹中，团队士气低落，但根基还在，宜收敛蓄力、守中待动"

# 通道①：尝试真实 LLM（配了 key 才生效）
real = try_real_llm(TEXT)
if real:
    vector, reason = real
    channel = "真实LLM"
else:
    # 通道②：主模型（Doubao）当场语义解码
    vector, reason = inject_vector(
        TEXT,
        (-1, -1, -1, -1, 0, -1, -1, 0, +1),
        "整体阴势敛藏：上显未成、主导受挫、刚健守收、不生发不通达；"
        "唯根基仍在(阳)而中爻蓄势持衡(0)，故机在收敛蓄力、守中待动。",
    )
    channel = "主模型(Doubao)直接解码"

print(f"语言：{TEXT}")
print(f"解码通道：{channel}")
print(f"目标向量：{list(vector)}")
print(f"解码理由：{reason}\n")

print("对比·旧关键词表：", list(T.language_to_vector(TEXT)))

hits = retrieve_with_oracle_from(TEXT, vector, top_n=2)
for h in hits:
    print(f"\n  命中 idx{h['idx']}(组{h['group_rep_idx']}) 欧氏距离 {h['dist']:.3f}  卦{h['hexagram']}")
    print(f"    象义「{h['oracle']['name']}」{h['oracle']['statement']}")
    print("    变爻断辞：")
    for y in h["yi"][:3]:
        print("      ", y["statement"])
