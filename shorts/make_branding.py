"""채널 프로필 이미지(800×800)와 배너(2560×1440)를 만든다.

    python3 shorts/make_branding.py   ->  shorts/branding/profile.png, banner.png
"""
from PIL import Image, ImageDraw

from make_short import CHANNEL, ROOT, background_size, draw_text, emoji_img

OUT = ROOT / "branding"
PURPLE = ((24, 16, 64), (88, 28, 135))
YELLOW = (255, 214, 0)


def profile():
    im = background_size(800, 800, *PURPLE)
    d = ImageDraw.Draw(im)
    # 원형으로 잘려 보이므로 가운데 지름 ~560 안에만 그린다
    d.ellipse((150, 150, 650, 650), fill=YELLOW)
    im.alpha_composite(emoji_img("🔍", 340), (230, 230))
    return im


def banner():
    W, H = 2560, 1440
    im = background_size(W, H, *PURPLE)
    # 양옆(데스크톱·TV에서만 보이는 영역)에 '다른 하나 찾기' 그리드 장식
    size, gap = 100, 28
    for side_x in (60, W - 60 - 3 * (size + gap)):
        for r in range(11):
            for c in range(3):
                odd = side_x > W / 2 and (r, c) == (7, 1) or side_x < W / 2 and (r, c) == (3, 2)
                tile = emoji_img("🥠" if odd else "🍪", size)
                im.alpha_composite(tile, (side_x + c * (size + gap), 26 + r * (size + gap)))
    # 모든 기기에서 보이는 안전 영역: 가운데 1546×423
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((W // 2 - 773, H // 2 - 211, W // 2 + 773, H // 2 + 211), radius=40,
                        fill=(24, 16, 64, 235))
    draw_text(d, (W // 2, H // 2 - 50), CHANNEL, 150, (255, 255, 255))
    draw_text(d, (W // 2, H // 2 + 110), "매일 저녁 6시 · 5초 안에 다른 하나 찾기", 62, YELLOW, stroke=6)
    return im


def main():
    OUT.mkdir(exist_ok=True)
    profile().convert("RGB").save(OUT / "profile.png")
    banner().convert("RGB").save(OUT / "banner.png", optimize=True)
    print(f"완료: {OUT}/profile.png, banner.png")


if __name__ == "__main__":
    main()
