# -*- coding: utf-8 -*-
"""语义解码器：自然语言 → 9 维三元向量。

替换关键词表的映射层。两条通道：
  ① 真实 LLM：配置 LLM_API_KEY / LLM_BASE_URL / LLM_MODEL 后，把三元公理与
     爻位语义写进 prompt，由大模型直接理解语言并输出 9 维向量（JSON）。
  ② 主模型注入：未配置 API 时，由对话主模型（Doubao 本身）当场语义解码，
     返回 (vector, reason)。这就是"大模型直接接入"——接入的即是我自己。

输出向量的值域与公理一致：每爻 ∈ {+1(显/生发/主动), 0(中和/蓄势/平衡), -1(隐/收敛/被动)}。
"""
from __future__ import annotations

import json
import os

# 爻位语义（公理1 + 位序象义，映射层）——供大模型理解语言时对齐
AXIS_MEANING = {
    1: "上爻·显于外/成/终局",
    2: "五爻·尊/主导/居位",
    3: "四爻·用/刚健/有为",
    4: "三爻·守/主动/持",
    5: "中爻·枢/势能平衡/蓄势",
    6: "六爻·升/生发/上行",
    7: "七爻·进/通达/交感",
    8: "八爻·蓄/显明于外",
    9: "初爻·基/根基/内藏",
}
STATE_MEANING = {
    "+1": "显、向外、生发、增益、主动",
    "0": "居间、耦合、过渡、稳态、势能平衡点",
    "-1": "隐、向内、收敛、减损、被动",
}


def _build_prompt(text: str) -> str:
    lines = [f"g{i} {AXIS_MEANING[i]}；取值：+1={STATE_MEANING['+1']}，"
             f"0={STATE_MEANING['0']}，-1={STATE_MEANING['-1']}"
             for i in range(1, 10)]
    return (
        "你是三元九爻符号系统的语义解码器。把下面这句话所描述的状态，"
        "映射为 g1..g9 九个爻的三元取值（+1/0/-1），严格按爻位语义理解，"
        "不要套模板，不要逐词匹配。只输出 JSON："
        '{"vector":[g1,g2,g3,g4,g5,g6,g7,g8,g9],"reason":"一句话"}。\n\n'
        "爻位语义：\n" + "\n".join(lines) +
        "\n\n待解码语言：「" + text + "」"
    )


def decode_with_real_llm(text: str, api_key=None, base_url=None,
                         model=None) -> tuple:
    """通道①：调用真实 LLM（OpenAI 兼容）解码。返回 (vector, reason)。"""
    from openai import OpenAI
    key = api_key or os.getenv("LLM_API_KEY", "")
    url = base_url or os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
    md = model or os.getenv("LLM_MODEL", "deepseek-chat")
    if not key:
        raise RuntimeError("未配置 LLM_API_KEY，无法调用真实 LLM")
    client = OpenAI(api_key=key, base_url=url)
    resp = client.chat.completions.create(
        model=md,
        messages=[{"role": "user", "content": _build_prompt(text)}],
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    data = json.loads(resp.choices[0].message.content)
    vec = tuple(int(x) for x in data["vector"])
    assert len(vec) == 9 and all(x in (-1, 0, 1) for x in vec), "非法向量"
    return vec, data.get("reason", "")


def try_real_llm(text: str):
    """若环境配置了真实 LLM 则解码，否则返回 None。"""
    if not os.getenv("LLM_API_KEY"):
        return None
    try:
        return decode_with_real_llm(text)
    except Exception as e:  # 调用失败不阻塞主模型注入
        return (None, f"real-llm 失败: {e}")


# 主模型注入入口：由对话中的大模型（Doubao）直接给出语义解码结果。
# 这是"接入大模型"的默认路径——接入的就是我自身。
def inject_vector(text: str, vector, reason: str):
    """把主模型当场解码得到的向量显式登记（与真实 LLM 通道统一出口）。"""
    assert len(vector) == 9 and all(x in (-1, 0, 1) for x in vector), "非法向量"
    return tuple(vector), reason
