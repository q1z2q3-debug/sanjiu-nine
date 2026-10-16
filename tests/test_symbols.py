"""三元九维符号体系单元测试（在 CI 中验证核心数理不被破坏）。

断言锁定公理（样例卦算子）、算子幂等、全集规模、等价组数与组分布。
"""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "trigram"))

from trigram import (F_C, F_Z, F_CZ, F_H, F_B_single,  # noqa: E402
                     build_universe, equivalence_groups)  # noqa: E402

# 公理单元测试样例卦
G = (1, 1, 0, -1, 1, 0, -1, -1, 0)


def test_fc():
    assert F_C(G) == (-1, -1, 0, 1, -1, 0, 1, 1, 0)


def test_fz():
    assert F_Z(G) == (0, -1, -1, 0, 1, -1, 0, 1, 1)


def test_fcz():
    assert F_CZ(G) == (0, 1, 1, 0, -1, 1, 0, -1, -1)


def test_fh_5dim():
    assert F_H(G) == (0, -1, 1, 0, -1)


def test_fb_single():
    # F_B_single 的 pos 为 1 基（第 N 爻）；第 5 爻动
    assert F_B_single(G, 5) == (1, 1, 0, -1, 0, 0, -1, -1, 0)


def test_involution():
    assert F_C(F_C(G)) == G
    assert F_Z(F_Z(G)) == G
    assert F_CZ(F_CZ(G)) == G


def test_universe_size():
    full = build_universe()[0]
    assert len(full) == 3 ** 9
    assert len(full) == 19683
    assert len(set(full)) == 19683


def test_equivalence_groups():
    total, groups, reps = equivalence_groups()
    assert total == 5002
    assert Counter(groups) == {1: 1, 2: 161, 4: 4840}
    assert len(reps) == total
    # Burnside 校验
    full = build_universe()[0]
    fix = {
        "e": len(full),
        "F_C": sum(1 for g in full if F_C(g) == g),
        "F_Z": sum(1 for g in full if F_Z(g) == g),
        "F_CZ": sum(1 for g in full if F_CZ(g) == g),
    }
    assert (fix["e"] + fix["F_C"] + fix["F_Z"] + fix["F_CZ"]) / 4 == total
