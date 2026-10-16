# -*- coding: utf-8 -*-
"""用权威编码表重建 19683 卦标准卦典，并挂接 729 份 docx 的卦辞文字。

编码规则（来自备份01/02 的 build_repo.py / repair.py / 三张编码表）：
  上卦表 UPN、中卦表 MIDN、下卦表 BOTN=MIDN，三表各 27 项互异（双射）。
  每卦由 (上U, 中M, 下B) 唯一确定：
      九爻向量 = DRT_MAP(UPN[U] + MIDN[M] + MIDN[B])，DRT→{D:-1,R:0,T:+1}
  卦辞文字按文件槽位 (U,M) 归属，卦内按九爻编号 B。
  错配处理：01上08中 的正文实为中卦 05 内容（repair.py OVERRIDE），
            故该份卦辞归属 (01,05,*)，(01,08,*) 卦辞缺失并标记。
"""
import csv
import json
import os
import re
import sys
import zipfile

SRC = "/tmp/sj729"
OUT_DIR = "/home/user/Doubao/chats/38446456964142338/trigram"
OUT_CSV = os.path.join(OUT_DIR, "sanjiu_quanji.csv")
OUT_JSON = os.path.join(OUT_DIR, "sanjiu_quanji.json")

DRT_MAP = {"D": -1, "R": 0, "T": 1}

# 权威编码表（与 build_repo.py / repair.py / data/*.csv 一致）
UPN = {'01': ('厚藏', 'DDD'), '02': ('待衡', 'DDR'), '03': ('启生', 'DDT'), '04': ('衡藏', 'DRD'),
       '05': ('双衡', 'DRR'), '06': ('启衡', 'DRT'), '07': ('基衡', 'RDD'), '08': ('基启', 'RDT'),
       '09': ('扬抑', 'TDD'), '10': ('扬衡', 'TDR'), '11': ('上下衡', 'RDR'), '12': ('扬启', 'TDT'),
       '13': ('抑扬', 'DTD'), '14': ('扬衡', 'DTR'), '15': ('奋生', 'DTT'), '16': ('双衡藏', 'RRD'),
       '17': ('全衡', 'RRR'), '18': ('衡启', 'RRT'), '19': ('抑衡', 'RTD'), '20': ('扬双衡', 'RTR'),
       '21': ('衡奋', 'RTT'), '22': ('基扬抑衡', 'TRD'), '23': ('基扬双衡', 'TRR'), '24': ('扬衡启', 'TRT'),
       '25': ('奋抑', 'TTD'), '26': ('奋衡', 'TTR'), '27': ('全扬', 'TTT')}
MIDN = {'01': ('厚藏', 'DDD'), '02': ('待衡', 'DDR'), '03': ('启生', 'DDT'), '04': ('衡藏', 'DRD'),
        '05': ('双衡', 'DRR'), '06': ('启衡', 'DRT'), '07': ('抑扬', 'DTD'), '08': ('扬衡', 'DTR'),
        '09': ('奋生', 'DTT'), '10': ('基衡', 'RDD'), '11': ('上下衡', 'RDR'), '12': ('基启', 'RDT'),
        '13': ('双衡藏', 'RRD'), '14': ('全衡', 'RRR'), '15': ('衡启', 'RRT'), '16': ('抑衡', 'RTD'),
        '17': ('扬双衡', 'RTR'), '18': ('衡奋', 'RTT'), '19': ('基扬抑', 'TDD'), '20': ('基扬衡', 'TDR'),
        '21': ('对扬', 'TDT'), '22': ('基扬抑衡', 'TRD'), '23': ('基扬双衡', 'TRR'), '24': ('扬衡启', 'TRT'),
        '25': ('奋抑', 'TTD'), '26': ('奋衡', 'TTR'), '27': ('全扬', 'TTT')}
BOTN = MIDN

# 文件槽位文字归属覆盖：(01上,08中) 正文实为中05 → 文字挂到中05
OVERRIDE = {('01', '08'): '05'}

FIELD_TAGS = ["九爻序列：", "复合卦总释", "分层拆解", "跨层制衡",
              "全局自适配能力评估", "演化路径"]


def paras_of(path):
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8", errors="ignore")
    ps = ["".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", p))
          for p in re.findall(r"<w:p[ >].*?</w:p>", xml, re.S)]
    return [t.strip() for t in ps if t.strip()]


def parse_doc(path):
    paras = paras_of(path)
    start = [i for i, t in enumerate(paras) if re.match(r"^\d\d｜\d\d｜\d\d\s", t)]
    out = {}
    for k, si in enumerate(start):
        ei = start[k + 1] if k + 1 < len(start) else len(paras)
        block = paras[si:ei]
        head = block[0]
        parts = head.split("｜")
        B = parts[2].split("　")[0].strip()
        name = head.split("　", 1)[1] if "　" in head else ""
        cur_tag, buf, fields = None, [], {}
        for t in block[1:]:
            matched = next((tag for tag in FIELD_TAGS if t.startswith(tag)), None)
            if matched:
                if cur_tag:
                    fields[cur_tag] = " ".join(buf).strip()
                cur_tag = matched
                buf = []
            elif cur_tag:
                buf.append(t)
        if cur_tag:
            fields[cur_tag] = " ".join(buf).strip()
        out[B] = {
            "B": B, "name": name,
            "zongshi": fields.get("复合卦总释", ""),
            "fenceng": fields.get("分层拆解", ""),
            "zhiheng": fields.get("跨层制衡", ""),
            "zishiying": fields.get("全局自适配能力评估", ""),
            "yanhua": fields.get("演化路径", ""),
        }
    return out


def vec_to_idx(vec):
    n = 0
    for v in vec:
        n = n * 3 + (v + 1)
    return n


def main():
    files = sorted(f for f in os.listdir(SRC) if f.endswith(".docx"))
    pf = re.compile(r"^三元九维19683体系_(\d{2})上(\d{2})中_全套27九爻卦\.docx$")
    # 1) 先用编码表重建全部 19683 卦的权威向量
    guas = {}
    for U in sorted(UPN):
        for M in sorted(MIDN):
            for B in sorted(BOTN):
                u3 = UPN[U][1]
                m3 = MIDN[M][1]
                b3 = BOTN[B][1]
                drt = u3 + m3 + b3
                vec = [DRT_MAP[c] for c in drt]
                idx = vec_to_idx(vec)
                guas[idx] = {
                    "idx": idx, "U": U, "Uname": UPN[U][0], "M": M, "Mname": MIDN[M][0],
                    "B": B, "Bname": BOTN[B][0],
                    "drt": list(drt), "vec": vec,
                    "name": "", "zongshi": "", "fenceng": "", "zhiheng": "",
                    "zishiying": "", "yanhua": "",
                    "has_text": False,
                }
    # 2) 挂接卦辞文字（按槽位；OVERRIDE 修正 01上08中 → 中05）
    text_missing = []
    for f in files:
        m = pf.match(f)
        if not m:
            continue
        U, M = m.groups()
        target_M = OVERRIDE.get((U, M), M)
        try:
            gtext = parse_doc(os.path.join(SRC, f))
        except Exception as e:
            text_missing.append((f, "解析失败 " + str(e)))
            continue
        if len(gtext) != 27:
            text_missing.append((f, "卦数=%d" % len(gtext)))
        for B, g in gtext.items():
            u3, m3, b3 = UPN[U][1], MIDN[target_M][1], BOTN[B][1]
            idx = vec_to_idx([DRT_MAP[c] for c in u3 + m3 + b3])
            rec = guas[idx]
            if not rec["has_text"]:  # 保留第一份（01上05中 的原文）
                for k in ("name", "zongshi", "fenceng", "zhiheng", "zishiying", "yanhua"):
                    rec[k] = g[k]
                rec["has_text"] = True
    # 3) 统计缺失
    missing = [idx for idx, r in guas.items() if not r["has_text"]]
    return guas, missing, text_missing


if __name__ == "__main__":
    guas, missing, text_missing = main()
    idxs = sorted(guas.keys())
    ok = idxs == list(range(19683))
    print(f"重建卦数: {len(guas)}，idx 覆盖 0..{idxs[-1]}：{'通过' if ok else '失败'}")
    print(f"卦辞覆盖: {19683 - len(missing)}/19683，缺失: {len(missing)}")
    if missing:
        # 缺失应集中在 (01,08,*) 27 卦
        first = guas[missing[0]]
        print(f"  缺失样例: 上{first['U']}{first['Uname']} 中{first['M']}{first['Mname']} idx={missing[0]}")
    print(f"文字解析问题: {len(text_missing)}")
    for t in text_missing[:3]:
        print("  ", t)
    # 写 CSV / JSON
    with open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["idx", "U", "Uname", "M", "Mname", "B", "Bname", "name",
                    "d1","d2","d3","d4","d5","d6","d7","d8","d9",
                    "v1","v2","v3","v4","v5","v6","v7","v8","v9",
                    "zongshi", "fenceng", "zhiheng", "zishiying", "yanhua", "has_text"])
        for i in idxs:
            r = guas[i]
            w.writerow([i, r["U"], r["Uname"], r["M"], r["Mname"], r["B"], r["Bname"],
                        r["name"]] + r["drt"] + r["vec"] +
                       [r["zongshi"], r["fenceng"], r["zhiheng"],
                        r["zishiying"], r["yanhua"], r["has_text"]])
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(guas, f, ensure_ascii=False, indent=0)
    print(f"已写出: {OUT_CSV} / {OUT_JSON}")
