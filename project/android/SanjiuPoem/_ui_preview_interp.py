# -*- coding: utf-8 -*-
"""生成"三元原创诗 + 正轨专业解读"界面示意预览（PIL 程序化排版，非截图）。"""
import json
from PIL import Image, ImageDraw, ImageFont

BASE = "/home/user/Doubao/chats/38446456964142338"
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"

BG, CARD, INK = (0xF6F1E7,), (0xFF, 0xFF, 0xFF), (0x26, 0x22, 0x1C)
ACCENT, GREEN, GRAY, BORDER = (0xB5, 0x43, 0x2A), (0x3E, 0x5C, 0x46), (0x8A, 0x82, 0x74), (0xE4, 0xDC, 0xCA)

def F(sz, bold=False):
    return ImageFont.truetype(FONT, sz, index=1 if bold else 0)

def wrap(draw, text, font, maxw):
    out, cur = [], ""
    for ch in text:
        if draw.textlength(cur + ch, font=font) > maxw and cur:
            out.append(cur); cur = ch
        else:
            cur += ch
    if cur: out.append(cur)
    return out

def draw_gua(d, x, y, w, h, gua, color):
    row = h / 9.0
    for i, v in enumerate(gua):
        cy = y + i * row + row / 2
        th = max(2, row * 0.30)
        if v == 1:
            d.rectangle([x, cy - th/2, x + w, cy + th/2], fill=color)
        elif v == -1:
            seg = (w - 6 - (w - 6) / 3) / 2
            d.rectangle([x+3, cy-th/2, x+3+seg, cy+th/2], fill=color)
            d.rectangle([x+w-3-seg, cy-th/2, x+w-3, cy+th/2], fill=color)
        else:
            d.line([x+3, cy, x+w-3, cy], fill=color, width=max(1, int(th*0.22)))
            s = th * 0.9; cx = x + w / 2
            d.polygon([(cx, cy-s),(cx+s, cy),(cx, cy+s),(cx-s, cy)], outline=color)

def main():
    poems = json.load(open(BASE + "/project/android/SanjiuPoem/app/src/main/assets/original.json"))
    p = [o for o in poems if o["title"] == "夕照"][0]
    W = 1000
    # 页面
    page = Image.new("RGB", (W, 1180), BG)
    d = ImageDraw.Draw(page)
    # 标题区
    d.text((44, 44), "三元九爻 · 年龄分类诗词", font=F(46, True), fill=INK)
    d.text((44, 104), "「老年」三元原创 · 诗卦驱动的创作诗", font=F(30, True), fill=GREEN)
    # 卡片
    cx, cy, cw, chh = 40, 170, W - 80, 940
    d.rounded_rectangle([cx, cy, cx+cw, cy+chh], 28, fill=CARD, outline=BORDER, width=3)
    # 卦画
    draw_gua(d, cx+46, cy+60, 74, 180, p["gua"], INK)
    d.text((cx+150, cy+62), "《夕照》· 动境界爻", font=F(38, True), fill=INK)
    d.rounded_rectangle([cx+150, cy+122, cx+150+140, cy+158], 12, fill=GREEN)
    d.text((cx+164, cy+124), "三元原创", font=F(26), fill=(255, 255, 255))
    # 正文
    body = p["text"].replace("\n", "  ")
    yy = cy + 210
    d.text((cx+46, yy), body, font=F(34), fill=INK)
    # 解读块
    yy = cy + 300
    d.rounded_rectangle([cx+46, yy, cx+46+96, yy+40], 12, fill=ACCENT)
    d.text((cx+66, yy+6), "解 读", font=F(28, True), fill=(255, 255, 255))
    yy += 56
    lines = wrap(d, p["interpretation"], F(27), cw - 92)
    for ln in lines[:10]:
        d.text((cx+46, yy), ln, font=F(27), fill=INK)
        yy += 46
    # 创作卦 meta
    d.text((cx+46, cy+chh-66), "创作卦 " + "[%s]" % ",".join(str(x) for x in p["gua"]), font=F(22), fill=GRAY)
    page.save(BASE + "/project/android/SanjiuPoem/interp_preview.png")
    print("已生成 interp_preview.png", page.size, "解读行数:", len(lines))

if __name__ == "__main__":
    main()
