# -*- coding: utf-8 -*-
"""PIL 预览：三元原创卡新增「卦典」块（点按展开深度卦辞）。"""
import json
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, "trigram")
from build_quanji import vec_to_idx

QUAN = json.load(open("project/android/SanjiuPoem/app/src/main/assets/sanjiu_quanji_apk.json", encoding="utf-8"))
J = json.load(open("project/android/SanjiuPoem/app/src/main/assets/original.json", encoding="utf-8"))

MIBAI = (246, 241, 231)
INK = (38, 34, 28)
ACCENT = (181, 67, 42)
GREEN = (62, 92, 70)
GRAY = (120, 114, 106)
CARD = (255, 253, 248)


def font(sz, bold=False):
    for p in ["/usr/share/fonts/truetype/noto/NotoSerifCJK-Bold.ttc",
              "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
              "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"]:
        try:
            return ImageFont.truetype(p, sz)
        except Exception:
            pass
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", sz)
    except Exception:
        return ImageFont.load_default()


def wrap(dr, text, f, maxw):
    lines, cur = [], ""
    for ch in text:
        if dr.textlength(cur + ch, font=f) > maxw:
            lines.append(cur); cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def main():
    W, H = 540, 640
    im = Image.new("RGB", (W, H), MIBAI)
    dr = ImageDraw.Draw(im)
    # 卡片
    dr.rounded_rectangle((20, 18, W - 20, H - 18), 14, fill=CARD, outline=(222, 214, 200))
    y = 40
    # 标题
    f16 = font(16, True); f13 = font(13); f12 = font(12)
    dr.text((40, y), "《夕照 · 动境界爻》 · 三元原创", font=f16, fill=INK); y += 34
    dr.rounded_rectangle((40, y, 90, y + 22), 11, fill=GREEN)
    dr.text((48, y + 3), "三元原创", font=font(12), fill=(255, 255, 255)); y += 34
    # 诗文本
    for ln in wrap(dr, "远山衔落日，归鸟入深林。", f13, W - 80):
        dr.text((40, y), ln, font=f13, fill=INK); y += 24
    y += 8
    # 解读坐标
    dr.text((40, y), "创作卦 [1,-1,0,-1,1,-1,-1,0,1] · 解读坐标：境界朗照…", font=f12, fill=GRAY); y += 22
    dr.text((40, y), "主旨显隐·诗旨深隐，情感强度·情感含蓄，……", font=f12, fill=GRAY); y += 28
    # 卦典块（朱砂）
    dr.text((40, y), "▶ 卦典 · 夕照动境界爻卦（点按展开）", font=f12, fill=ACCENT); y += 26
    dr.line((40, y, W - 40, y), fill=(222, 214, 200)); y += 14
    # 展开内容（截断示意）
    for ln in ["【复合卦总释】本卦底层承载封存、中层增益递送、上层审定回灌…（展开见完整卦辞）",
               "【分层拆解】下卦底盘… 中卦枢纽… 上卦大势…",
               "【跨层制衡】…　【全局自适配能力评估】…　【演化路径】…"]:
        for sub in wrap(dr, ln, f12, W - 80):
            dr.text((40, y), sub, font=f12, fill=INK); y += 20
    y += 6
    # 人类卦辞块（松花绿）：母结构 → 人类认知语言
    dr.text((40, y), "▶ 人类卦辞 · 中·无咎·沉静扬卦（点按展开）", font=f12, fill=GREEN); y += 26
    dr.line((40, y, W - 40, y), fill=(222, 214, 200)); y += 14
    for ln in ["【传统卦辞】下卦沉观发，其基阴阳参差动静相济；…中卦守中明，其枢衡众居中审时待机；上卦敛度扬，其势…。无咎，中和守正。",
               "【通俗释义】此卦下盘沉潜、观察、萌发，…中道固守、中正、昭明，…上势收束、权衡、外扬，…。阴阳中和，动静相济，守正无咎。",
               "【生活启示】守中持衡，不偏不倚。"]:
        for sub in wrap(dr, ln, f12, W - 80):
            dr.text((40, y), sub, font=f12, fill=INK); y += 20
    im.save("/tmp/quanji_preview.png")
    print("saved /tmp/quanji_preview.png")


if __name__ == "__main__":
    main()
