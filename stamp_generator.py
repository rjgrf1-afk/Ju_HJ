"""한글 회사/이름 도장(직인) 이미지 생성기.

4글자 상호는 전통 인장 배치(우→좌, 상→하 순서로 읽는 2x2 배열)를 따르고,
그 외 글자 수는 세로 한 줄로 배치한다. 배경은 투명(PNG)이라 전자문서에
바로 붙여 쓸 수 있다.
"""

import math
from PIL import Image, ImageDraw, ImageFont

FONT_PATHS = [
    "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
    "C:/Windows/Fonts/malgunbd.ttf",
    "C:/Windows/Fonts/malgun.ttf",
]

INK_RED = (194, 27, 40, 255)
SUPERSAMPLE = 4


def _load_font(size):
    for path in FONT_PATHS:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _draw_char(draw, ch, cx, cy, font_size, color):
    font = _load_font(font_size)
    bbox = draw.textbbox((0, 0), ch, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((cx - w / 2 - bbox[0], cy - h / 2 - bbox[1]), ch, font=font, fill=color)


def generate_seal(name, shape="round", size=600, rotate=False):
    """name(상호/이름)을 도장 이미지(RGBA, 투명 배경)로 렌더링해 반환한다.

    shape: "round"(원형) 또는 "square"(사각형)
    """
    name = "".join(name.split())
    if not name:
        name = "인"

    S = size * SUPERSAMPLE
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    margin = int(S * 0.07)
    outer_w = max(2, int(S * 0.02))
    gap = int(S * 0.03)
    inner_w = max(2, int(S * 0.012))

    box_outer = [margin, margin, S - margin, S - margin]
    box_inner = [margin + gap, margin + gap, S - margin - gap, S - margin - gap]

    if shape == "square":
        radius = int(S * 0.05)
        draw.rounded_rectangle(box_outer, radius=radius, outline=INK_RED, width=outer_w)
        draw.rounded_rectangle(box_inner, radius=int(radius * 0.75), outline=INK_RED, width=inner_w)
    else:
        draw.ellipse(box_outer, outline=INK_RED, width=outer_w)
        draw.ellipse(box_inner, outline=INK_RED, width=inner_w)

    cx = cy = S / 2
    chars = list(name)
    n = len(chars)
    half_inner = (box_inner[2] - box_inner[0]) / 2

    if n == 4:
        # 전통 인장 배치: 우측 상->하, 좌측 상->하 순으로 읽는다 (예: 극동전기)
        offset = half_inner * 0.47
        font_size = int(S * 0.27)
        positions = [
            (cx + offset, cy - offset),  # 1번째 글자: 우상
            (cx + offset, cy + offset),  # 2번째 글자: 우하
            (cx - offset, cy - offset),  # 3번째 글자: 좌상
            (cx - offset, cy + offset),  # 4번째 글자: 좌하
        ]
        for ch, (px, py) in zip(chars, positions):
            _draw_char(draw, ch, px, py, font_size, INK_RED)
    else:
        size_ratio = {1: 0.42, 2: 0.3, 3: 0.23}.get(n, max(0.12, 0.7 / n))
        font_size = int(S * size_ratio)
        spacing = font_size * 1.05
        total_h = spacing * (n - 1)
        start_y = cy - total_h / 2
        for i, ch in enumerate(chars):
            _draw_char(draw, ch, cx, start_y + i * spacing, font_size, INK_RED)

    if rotate:
        import random

        img = img.rotate(random.uniform(-2.2, 2.2), resample=Image.BICUBIC, expand=False)

    img = img.resize((size, size), Image.LANCZOS)
    return img


if __name__ == "__main__":
    import sys

    name = sys.argv[1] if len(sys.argv) > 1 else "극동전기"
    generate_seal(name, "round").save(f"{name}_원형.png")
    generate_seal(name, "square").save(f"{name}_사각.png")
