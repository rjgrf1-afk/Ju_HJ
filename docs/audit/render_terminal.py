"""명령 출력 텍스트를 터미널처럼 보이는 PNG로 그린다 (감사 증빙용).

사용법:
    python3 docs/audit/render_terminal.py --cmd "python3 shorts/channel_report.py" \
        --caption "Section d) ..." --input out.txt --output docs/audit/evidence/d.png
"""
import argparse
import unicodedata
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
MONO_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
WIDE = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"  # 한글은 DejaVu에 없어 2칸 폭으로 대체
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"  # 비트맵 글꼴이라 109px로만 그려진다
SIZE, PAD, LINE = 22, 40, 32
BG, FG, PROMPT, CAPTION, BAR = "#1e1e1e", "#d4d4d4", "#6a9955", "#ffffff", "#2d2d2d"
MIN_WIDTH = 1600


def is_wide(c):
    return unicodedata.east_asian_width(c) in "WF"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cmd", required=True)
    ap.add_argument("--caption", required=True)
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    mono = ImageFont.truetype(MONO, SIZE)
    bold = ImageFont.truetype(MONO_BOLD, SIZE)
    wide = ImageFont.truetype(WIDE, SIZE)
    emoji = ImageFont.truetype(EMOJI, 109)
    cell = mono.getlength("M")

    lines = Path(args.input).read_text().rstrip("\n").split("\n")
    cols = max(sum(2 if is_wide(c) else 1 for c in l) for l in [args.cmd + "$ ", *lines])
    width = max(MIN_WIDTH, int(cols * cell) + 2 * PAD)
    bar_h = 70
    height = bar_h + PAD + LINE * (len(lines) + 2) + PAD

    img = Image.new("RGB", (width, height), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, width, bar_h], fill=BAR)
    d.text((PAD, bar_h / 2), args.caption, font=bold, fill=CAPTION, anchor="lm")

    def draw(y, text, fill):
        x = PAD
        for c in text:
            if ord(c) >= 0x1F000:
                glyph = Image.new("RGBA", (136, 128))
                ImageDraw.Draw(glyph).text((0, 0), c, font=emoji, embedded_color=True)
                glyph = glyph.crop(glyph.getbbox()).resize((SIZE + 2, SIZE + 2))
                img.paste(glyph, (int(x + (2 * cell - SIZE) / 2), y + 3), glyph)
                x += 2 * cell
            elif is_wide(c):
                d.text((x, y), c, font=wide, fill=fill)
                x += 2 * cell
            else:
                d.text((x, y), c, font=mono, fill=fill)
                x += cell

    y = bar_h + PAD
    d.text((PAD, y), "$ ", font=bold, fill=PROMPT)
    draw(y, "  " + args.cmd, FG)
    for line in lines:
        y += LINE
        draw(y, line, FG)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    img.save(args.output)
    print(f"{args.output} ({width}x{height})")


if __name__ == "__main__":
    main()
