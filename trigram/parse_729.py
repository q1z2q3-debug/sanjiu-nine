# -*- coding: utf-8 -*-
"""解析"三元九维19683体系_729份19683卦"docx 全集 → 结构化卦典数据。

适配映射（自定义）：文档爻态为功能三元 D/R/T
  D=承载·削减·封存（收敛向内） → -1（阴·隐）
  R=审定·评估·分辨·回灌（居间审视）→  0（中和·衡）
  T=增益·势能·递送（生发向外） → +1（阳·显）
适配后可与 19683 卦向量一一对齐检索；文档文字保留其"承载/审定/增益"语义，作为参考象义层。
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
    # 卦名行：NN｜NN｜NN　卦名
    start = [i for i, t in enumerate(paras) if re.match(r"^\d\d｜\d\d｜\d\d\s", t)]
    guas = []
    for k, si in enumerate(start):
        ei = start[k + 1] if k + 1 < len(start) else len(paras)
        block = paras[si:ei]
        head = block[0]
        name = head.split("　", 1)[1] if "　" in head else head.split(" ", 1)[1]
        # 字段
        fields = {}
        cur_tag = None
        buf = []
        for t in block[1:]:
            matched = next((tag for tag in FIELD_TAGS if t.startswith(tag)), None)
            if matched:
                if cur_tag:
                    fields[cur_tag] = " ".join(buf)
                cur_tag = matched
                buf = [t[len(matched):].strip()] if matched == "九爻序列：" else []
            elif cur_tag:
                buf.append(t)
        if cur_tag:
            fields[cur_tag] = " ".join(buf)
        seq_raw = fields.get("九爻序列：", "")
        drt = re.sub(r"[^DRT]", "", seq_raw)
        if len(drt) != 9:
            print(f"  !! 九爻序列异常({len(drt)}): {path} {head}", file=sys.stderr)
            drt = drt[:9].ljust(9, "D")
        vec = [DRT_MAP[c] for c in drt]
        guas.append({
            "head": head, "name": name, "drt": list(drt), "vec": vec,
            "zongshi": fields.get("复合卦总释", ""),
            "fenceng": fields.get("分层拆解", ""),
            "zhiheng": fields.get("跨层制衡", ""),
            "zishiying": fields.get("全局自适配能力评估", ""),
            "yanhua": fields.get("演化路径", ""),
        })
    return guas


def vec_to_idx(vec):
    n = 0
    for v in vec:
        n = n * 3 + (v + 1)
    return n


def main(limit=None):
    files = sorted(f for f in os.listdir(SRC) if f.endswith(".docx"))
    if limit:
        files = files[:limit]
    records = {}
    err = []
    for f in files:
        path = os.path.join(SRC, f)
        try:
            guas = parse_doc(path)
            if len(guas) != 27:
                err.append((f, f"卦数={len(guas)}"))
            for g in guas:
                idx = vec_to_idx(g["vec"])
                if idx in records:
                    err.append((f, f"idx重复 {idx}"))
                records[idx] = {**g, "idx": idx, "file": f}
        except Exception as e:
            err.append((f, str(e)))
    return records, err


if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    recs, err = main(limit)
    print(f"解析卦数: {len(recs)}，错误: {len(err)}")
    for e in err[:10]:
        print("  ERR", e)
    if limit:
        if len(sys.argv) > 2:
            import pprint
            pprint.pprint(list(recs.values())[0])
    else:
        # 校验覆盖
        idxs = sorted(recs.keys())
        assert idxs == list(range(19683)), "idx 未全覆盖 0..19682"
        # 写 CSV
        with open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(["idx", "name", "d1","d2","d3","d4","d5","d6","d7","d8","d9",
                        "v1","v2","v3","v4","v5","v6","v7","v8","v9",
                        "zongshi", "fenceng", "zhiheng", "zishiying", "yanhua"])
            for i in idxs:
                g = recs[i]
                w.writerow([g["idx"], g["name"]] + g["drt"] + g["vec"]
                           + [g["zongshi"], g["fenceng"], g["zhiheng"],
                              g["zishiying"], g["yanhua"]])
        # 写 JSON
        with open(OUT_JSON, "w", encoding="utf-8") as f:
            json.dump(recs, f, ensure_ascii=False, indent=1)
        print(f"已写出: {OUT_CSV} / {OUT_JSON}")
        print(f"行数={len(idxs)}，idx 覆盖 0..{idxs[-1]}，重复错误={len(err)}")

