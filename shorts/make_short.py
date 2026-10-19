"""눈썰미 테스트 쇼츠 자동 생성기.

사용법:
    python3 shorts/make_short.py                # 오늘 날짜(KST) 영상 생성
    python3 shorts/make_short.py --date 2026-10-20

결과: shorts/output/<날짜>/ 에 short.mp4, preview.png, metadata.json
같은 날짜는 항상 같은 영상이 나온다(날짜 기반 시드).
"""
import argparse
import json
import math
import random
import subprocess
import wave
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "output"
HISTORY = ROOT / "history.json"

W, H, FPS = 1080, 1920, 30
SR = 44100
ROUND_SHOW, ROUND_REVEAL, OUTRO = 5.0, 1.5, 1.6

# 쇼츠 UI(우측 버튼, 하단 제목)를 피한 그리드 영역
GRID_X, GRID_Y, GRID_SIZE = 70, 600, 860

EMOJI_FONT = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
KO_FONTS = [
    "/usr/share/fonts/truetype/nanum/NanumGothicExtraBold.ttf",
    "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "C:/Windows/Fonts/malgunbd.ttf",
]

EASY = ["🍎🍏", "🐶🐱", "⚽🏀", "🍋🍊", "🐻🐼", "🦊🐶", "🎈🎀", "🍩🥯",
        "🌹🌷", "🚗🚙", "🐢🦎", "🍪🥠", "🥑🥝", "🐟🐠", "🌑🌚"]
MEDIUM = ["🙂🙃", "📕📙", "🔒🔓", "🌲🌳", "🐑🐏", "💛🧡", "😺😸", "⭐🌟",
          "🌕🌝", "🌻🌼", "😴😪", "😬😁"]
HARD = ["😀😃", "🕐🕑", "😮😯", "🐥🐤", "😐😑"]
# 좌우가 비대칭이라 뒤집으면 티가 (조금) 나는 이모지
MIRROR = ["🐟", "🐢", "🦎", "🚗", "🐥", "🦒", "🐌", "🦕", "🐎", "🦜", "🐧", "🚀"]

THEMES = [  # (배경 위, 배경 아래, 강조색)
    ((24, 16, 64), (88, 28, 135), (255, 214, 0)),
    ((6, 40, 72), (14, 116, 144), (255, 94, 98)),
    ((20, 20, 20), (60, 60, 70), (0, 230, 160)),
    ((90, 20, 40), (190, 60, 70), (255, 236, 130)),
    ((10, 60, 40), (30, 130, 90), (255, 255, 255)),
]

TITLES = [
    "다른 하나 찾기 🔍 3단계 성공하면 상위 1%",
    "99%가 3단계에서 포기하는 눈썰미 테스트 👀",
    "5초 안에 다른 하나 찾으면 천재 🧠",
    "이거 다 찾으면 눈썰미 상위 1% 인정 🏆",
    "3단계는 진짜 못 찾음... 도전? 🔥",
]
HASHTAGS = ["#shorts", "#눈썰미테스트", "#다른그림찾기", "#퀴즈", "#두뇌게임",
            "#findtheodd", "#brainteaser", "#puzzle"]


def ko_font(size):
    for p in KO_FONTS:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


_emoji_font = ImageFont.truetype(EMOJI_FONT, 109)
_emoji_cache = {}


def emoji_img(ch, size, mirror=False):
    key = (ch, size, mirror)
    if key not in _emoji_cache:
        im = Image.new("RGBA", (136, 128), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((0, 0), ch, font=_emoji_font, embedded_color=True)
        im = im.crop(im.getbbox()).resize((size, size), Image.LANCZOS)
        if mirror:
            im = ImageOps.mirror(im)
        _emoji_cache[key] = im
    return _emoji_cache[key]


def draw_text(d, xy, text, size, fill, anchor="mm", stroke=8):
    # 얇은 폰트를 같은 색 외곽선으로 굵게 만들고, 아래에 그림자를 깐다
    font, bold = ko_font(size), max(1, size // 45)
    if stroke:
        d.text((xy[0] + 5, xy[1] + 7), text, font=font, fill=(0, 0, 0), anchor=anchor,
               stroke_width=bold + stroke // 2, stroke_fill=(0, 0, 0))
    d.text(xy, text, font=font, fill=fill, anchor=anchor, stroke_width=bold, stroke_fill=fill)


# ---------- 라운드 구성 ----------

def pick(rng, pool, used):
    fresh = [p for p in pool if p not in used]
    return rng.choice(fresh or pool)


def build_rounds(rng, used):
    a = pick(rng, EASY, used)
    b = pick(rng, MEDIUM, used)
    kind = rng.choice(["hard", "mirror", "color"])
    rounds = [
        {"kind": "emoji", "pair": a, "n": 5, "label": "1단계 · 쉬움"},
        {"kind": "emoji", "pair": b, "n": 7, "label": "2단계 · 보통"},
    ]
    if kind == "hard":
        rounds.append({"kind": "emoji", "pair": pick(rng, HARD, used), "n": 8, "label": "3단계 · 극악"})
    elif kind == "mirror":
        rounds.append({"kind": "mirror", "pair": pick(rng, MIRROR, used), "n": 8, "label": "3단계 · 극악"})
    else:
        rounds.append({"kind": "color", "pair": None, "n": 7, "label": "3단계 · 극악"})
    for r in rounds:
        if rng.random() < 0.5 and r["kind"] == "emoji":
            r["pair"] = r["pair"][::-1] if len(r["pair"]) == 2 else r["pair"]
        r["answer"] = rng.randrange(r["n"] * r["n"])
    return rounds


def render_grid(r, rng):
    """그리드 이미지(RGBA)와 정답 칸의 중심/반지름을 돌려준다."""
    n = r["n"]
    cell = GRID_SIZE / n
    pad = cell * 0.12
    im = Image.new("RGBA", (GRID_SIZE, GRID_SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, GRID_SIZE - 1, GRID_SIZE - 1), radius=40, fill=(255, 255, 255, 235))
    size = int(cell - pad * 2)

    if r["kind"] == "color":
        h = rng.random()
        import colorsys
        base = colorsys.hsv_to_rgb(h, 0.65, 0.85)
        odd = colorsys.hsv_to_rgb(h, 0.65, 0.85 + 0.075)
        base = tuple(int(c * 255) for c in base)
        odd = tuple(int(min(c, 1) * 255) for c in odd)

    for i in range(n * n):
        x = int(i % n * cell + pad)
        y = int(i // n * cell + pad)
        is_odd = i == r["answer"]
        if r["kind"] == "color":
            d.rounded_rectangle((x, y, x + size, y + size), radius=size // 5,
                                fill=odd if is_odd else base)
        elif r["kind"] == "mirror":
            im.alpha_composite(emoji_img(r["pair"], size, mirror=is_odd), (x, y))
        else:
            ch = r["pair"][1] if is_odd else r["pair"][0]
            im.alpha_composite(emoji_img(ch, size), (x, y))

    cx = GRID_X + (r["answer"] % n + 0.5) * cell
    cy = GRID_Y + (r["answer"] // n + 0.5) * cell
    return im, (cx, cy, cell * 0.62)


# ---------- 프레임 ----------

def background(theme):
    top, bottom, _ = theme
    g = np.linspace(0, 1, H)[:, None]
    arr = (np.array(top) * (1 - g) + np.array(bottom) * g)
    arr = np.repeat(arr[:, None, :], W, axis=1).astype(np.uint8)
    return Image.fromarray(arr, "RGB").convert("RGBA")


def header(base, theme, label):
    d = ImageDraw.Draw(base)
    draw_text(d, (W // 2, 230), "다른 하나를 찾아라!", 92, (255, 255, 255))
    draw_text(d, (W // 2, 360), "3단계 성공하면 상위 1%", 58, theme[2], stroke=6)
    d.rounded_rectangle((W // 2 - 210, 455, W // 2 + 210, 545), radius=45, fill=(0, 0, 0, 150))
    draw_text(d, (W // 2, 500), label, 50, (255, 255, 255), stroke=0)


def make_round_frames(r, grid, ans, bg, theme):
    base = bg.copy()
    header(base, theme, r["label"])
    base.alpha_composite(grid, (GRID_X, GRID_Y))

    show_n = int(ROUND_SHOW * FPS)
    bar_y = GRID_Y + GRID_SIZE + 70
    for f in range(show_n):
        t = f / FPS
        im = base.copy()
        d = ImageDraw.Draw(im)
        frac = 1 - t / ROUND_SHOW
        d.rounded_rectangle((GRID_X, bar_y, GRID_X + GRID_SIZE, bar_y + 36), radius=18, fill=(0, 0, 0, 120))
        if frac > 0:
            col = theme[2] if frac > 0.3 else (255, 70, 70)
            d.rounded_rectangle((GRID_X, bar_y, GRID_X + max(36, int(GRID_SIZE * frac)), bar_y + 36),
                                radius=18, fill=col)
        sec = math.ceil(ROUND_SHOW - t)
        pop = 1 + 0.25 * max(0, 1 - (t % 1) * 4)  # 초가 바뀔 때 숫자가 툭 튀어나옴
        draw_text(d, (W // 2, bar_y + 150), str(sec), int(110 * pop), (255, 255, 255))
        yield im

    # 정답 공개: 나머지는 어둡게, 정답에 링
    cx, cy, rad = ans
    reveal = base.copy()
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shade)
    sd.rectangle((GRID_X, GRID_Y, GRID_X + GRID_SIZE, GRID_Y + GRID_SIZE), fill=(0, 0, 0, 140))
    sd.ellipse((cx - rad, cy - rad, cx + rad, cy + rad), fill=(0, 0, 0, 0))
    reveal.alpha_composite(shade)
    for f in range(int(ROUND_REVEAL * FPS)):
        im = reveal.copy()
        d = ImageDraw.Draw(im)
        grow = min(1, f / 6)
        rr = rad * (1.6 - 0.6 * grow)
        d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=(255, 40, 40), width=14)
        draw_text(d, (W // 2, bar_y + 150), "정답!", 110, (255, 230, 60))
        yield im


def make_outro_frames(bg, theme):
    base = bg.copy()
    d = ImageDraw.Draw(base)
    draw_text(d, (W // 2, 760), "몇 단계까지", 120, (255, 255, 255))
    draw_text(d, (W // 2, 910), "찾았어요?", 120, (255, 255, 255))
    draw_text(d, (W // 2, 1100), "댓글로 알려주세요", 70, theme[2], stroke=6)
    for _ in range(int(OUTRO * FPS)):
        yield base


# ---------- 사운드 (직접 합성, 저작권 걱정 없음) ----------

def tone(freq, dur, decay, vol):
    t = np.arange(int(SR * dur)) / SR
    return vol * np.sin(2 * np.pi * freq * t) * np.exp(-t * decay)


def make_audio(total, n_rounds, path):
    a = np.zeros(int(SR * total) + SR)

    def add(sig, at):
        i = int(at * SR)
        a[i:i + len(sig)] += sig[: len(a) - i]

    # 잔잔한 배경 아르페지오
    notes = [261.6, 329.6, 392.0, 523.3, 392.0, 329.6]
    beat = 0.25
    for k in range(int(total / beat)):
        add(tone(notes[k % len(notes)], 0.4, 6, 0.06), k * beat)
    t0 = 0.0
    for _ in range(n_rounds):
        for s in range(int(ROUND_SHOW)):
            hi = s == int(ROUND_SHOW) - 1
            add(tone(1500 if hi else 1000, 0.08, 40, 0.35), t0 + s)
        ding = tone(880, 0.8, 5, 0.35) + tone(1320, 0.8, 6, 0.2)
        add(ding, t0 + ROUND_SHOW)
        t0 += ROUND_SHOW + ROUND_REVEAL
    add(tone(660, 0.5, 4, 0.3) + tone(990, 0.5, 4, 0.2), t0)
    a = np.clip(a, -1, 1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((a * 32767).astype(np.int16).tobytes())


# ---------- 메타데이터 ----------

def make_metadata(rng, date, rounds):
    title = rng.choice(TITLES)
    desc = "\n".join([
        "5초 안에 다른 하나를 찾아보세요! 단계가 올라갈수록 어려워집니다 🔍",
        "몇 단계까지 찾았는지 댓글로 남겨주세요 👇",
        "매일 새로운 눈썰미 테스트가 올라옵니다. 구독하고 매일 도전하세요!",
        "",
        "Find the odd one out in 5 seconds! How far can you get?",
        "",
        " ".join(HASHTAGS),
    ])
    return {
        "date": date,
        "title": f"{title} #shorts"[:100],
        "description": desc,
        "tags": [h.lstrip("#") for h in HASHTAGS] + ["눈썰미", "숨은그림찾기", "odd one out"],
        "categoryId": "24",  # Entertainment
        "madeForKids": False,
        "containsSyntheticMedia": False,  # 실사처럼 보이는 합성물이 아니라 표시 대상 아님
        "rounds": [{"kind": r["kind"], "pair": r["pair"], "grid": r["n"],
                    "answer_row": r["answer"] // r["n"] + 1, "answer_col": r["answer"] % r["n"] + 1}
                   for r in rounds],
    }


def main():
    ap = argparse.ArgumentParser()
    kst_today = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d")
    ap.add_argument("--date", default=kst_today)
    args = ap.parse_args()

    rng = random.Random(f"nunsseulmi-{args.date}")
    history = json.loads(HISTORY.read_text()) if HISTORY.exists() else {}
    used = {p for d, ps in history.items() if d != args.date for p in ps}

    rounds = build_rounds(rng, used)
    theme = THEMES[rng.randrange(len(THEMES))]
    bg = background(theme)

    out = OUT_DIR / args.date
    out.mkdir(parents=True, exist_ok=True)
    total = len(rounds) * (ROUND_SHOW + ROUND_REVEAL) + OUTRO
    wav = out / "audio.wav"
    make_audio(total, len(rounds), wav)

    mp4 = out / "short.mp4"
    proc = subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", str(wav),
        "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", str(mp4),
    ], stdin=subprocess.PIPE)

    preview = None
    for r in rounds:
        grid, ans = render_grid(r, rng)
        for k, frame in enumerate(make_round_frames(r, grid, ans, bg, theme)):
            rgb = frame.convert("RGB")
            if preview is None and r is rounds[-1] and k == 0:
                preview = rgb
            proc.stdin.write(rgb.tobytes())
    for frame in make_outro_frames(bg, theme):
        proc.stdin.write(frame.convert("RGB").tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise SystemExit("ffmpeg 인코딩 실패")
    wav.unlink()
    preview.save(out / "preview.png")

    meta = make_metadata(rng, args.date, rounds)
    (out / "metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    history[args.date] = [r["pair"] for r in rounds if r["pair"]]
    HISTORY.write_text(json.dumps(dict(sorted(history.items())), ensure_ascii=False, indent=1))
    print(f"완료: {mp4} ({total:.1f}초)  제목: {meta['title']}")


if __name__ == "__main__":
    main()
