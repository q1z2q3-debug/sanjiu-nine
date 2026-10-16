# -*- coding: utf-8 -*-
"""桥接层：三元九爻符号层 ↔ capital-agent 认知层。

结构事实：capital-agent 认知层的状态格子（9 维三元 trit）与三元九爻的卦
是同一个 3^9 = 19683 空间，仅语义轴解释不同（认知层=任务维度，符号层=爻位象义）。
因此可只读桥接——把 agent 每个决策状态译为一个卦，用 错/综/错综/互/变爻断辞/象义
去"读"它，作为认知状态的**符号注解层**。本层不修改任何已交付的认知层逻辑。

用法：把 capital-agent 的 trit 字符串（每字符 '0'/'1'/'2'，对应 -1/0/+1）
映射为三元卦，经 oracle / yi_divination 给出注解。
"""
from __future__ import annotations

import sys
import os

# 使 capital-agent 与 trigram 可 import（脚本常从 capital-agent/ 根运行）
_HERE = os.path.dirname(os.path.abspath(__file__))
_CAP_SRC = os.path.join(_HERE, "src")
_TRIGRAM = os.path.dirname(_HERE) + "/trigram"
for p in (_CAP_SRC, _TRIGRAM):
    if p not in sys.path:
        sys.path.insert(0, p)

from oracle import oracle, representative_idx, yi_divination  # noqa: E402
import trigram as T  # noqa: E402


def trit_to_hex(trit) -> tuple:
    """capital-agent trit（'0'/'1'/'2' 字符串）→ 三元卦 tuple（{-1,0,+1}）。"""
    s = str(trit)
    return tuple(int(c) - 1 for c in s)


def hex_to_trit(g) -> str:
    """三元卦 tuple → capital-agent trit 字符串。"""
    return "".join(str(x + 1) for x in g)


def cognitive_oracle(trit):
    """把认知层状态 trit 译为一个卦，返回卦象注解（象义 + 等价组 + 断辞）。"""
    g = trit_to_hex(trit)
    return {
        "trit": str(trit),
        "hexagram": g,
        "idx": T.g_to_idx(g),
        "group_rep_idx": representative_idx(T.g_to_idx(g)),
        "oracle": oracle(g),
        "yi": yi_divination(g),
    }


def annotate_history(history: list, keys=("from", "to")):
    """对决策轨迹逐状态做卦象注解。"""
    return {k: cognitive_oracle(h.get(k)) for k in keys for h in history}
