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

from emoji_pool import EASY, HARD, ICON_NAMES, ICON_PAIRS, MEDIUM, MIRROR, NAMES

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "output"
HISTORY = ROOT / "history.json"

W, H, FPS = 1080, 1920, 30
SR = 44100
ROUND_SHOW, ROUND_REVEAL, OUTRO = 5.0, 1.5, 1.6
HOOK = 1.2  # 첫 화면: 3단계 문제를 먼저 보여 줘서 넘기지 않게 붙잡는다
CHANNEL = "눈썰미 연구소"

# 쇼츠 UI(우측 버튼, 하단 제목)를 피한 그리드 영역
GRID_X, GRID_Y, GRID_SIZE = 70, 600, 860

EMOJI_FONT = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
KO_FONTS = [
    "/usr/share/fonts/truetype/nanum/NanumGothicExtraBold.ttf",
    "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "C:/Windows/Fonts/malgunbd.ttf",
]

COLOR_NAMES = [(0.04, "빨간"), (0.11, "주황"), (0.19, "노란"), (0.30, "연두"), (0.43, "초록"),
               (0.52, "청록"), (0.60, "하늘색"), (0.70, "파란"), (0.80, "보라"), (0.92, "분홍"), (1.01, "빨간")]


THEMES = [  # (배경 위, 배경 아래, 강조색)
    ((24, 16, 64), (88, 28, 135), (255, 214, 0)),
    ((6, 40, 72), (14, 116, 144), (255, 94, 98)),
    ((20, 20, 20), (60, 60, 70), (0, 230, 160)),
    ((90, 20, 40), (190, 60, 70), (255, 236, 130)),
    ((10, 60, 40), (30, 130, 90), (255, 255, 255)),
]

HANDLE = "@nunsseulmi_lab"
# 흔한 "상위 1%" 대신 3단계 문제를 구체적으로 말해 주는 제목
# 영상마다 3단계 소재 이름이 들어가서 제목이 겹치지 않는다
HOOKS = {
    "mirror": "{name} {n}개 중 하나만 좌우가 뒤집혀 있어요 {e}",
    "emoji": "{name} {n}개 중 딱 하나가 달라요 {e}",
    "color": "{name} {n}칸 중 딱 한 칸만 색이 달라요 🎨",
    "icon": "{name} 아이콘 {n}개 중 딱 하나가 달라요 👀",
}
TAILS = ["3단계까지 찾을 수 있나요?", "마지막 문제에서 다들 멈춰요", "5초 안에 찾아보세요",
         "몇 단계까지 보이세요?", "3단계는 진짜 안 보여요"]
HASHTAGS = ["#shorts", "#눈썰미테스트", "#다른그림찾기", "#퀴즈", "#두뇌게임",
            "#findtheodd", "#brainteaser", "#puzzle"]
# 해외 시청자는 자기 나라 말로 된 제목을 본다 (해외 상위 퍼즐 채널은 20개 언어 안팎으로 단다)
# 소재 이름 대신 이모지를 넣어서 어느 나라에서나 같은 뜻이 되게 한다
LOCALES = {
    "en": {
        "label": "영어",
        "prefix": "Find the Odd One Out:",
        "hooks": {"emoji": "only 1 of these {n} {e} is different 👀",
                  "mirror": "only 1 of these {n} {e} is flipped ↔️",
                  "color": "only 1 of these {n} squares is a different color 🎨",
                  "icon": "only 1 of these {n} icons is different 👀"},
        "tails": ["Can you beat level 3?", "Most people get stuck at level 3",
                  "Find it in 5 seconds", "How far can you get?"],
        "desc": ["Find the odd one out in 5 seconds! It gets harder every level 🔍",
                 "Comment how far you got 👇",
                 "A new eye test every day. Subscribe and play daily!"],
        "tags": ["#oddoneout", "#findthedifference", "#brainteaser", "#puzzle"],
    },
    "ja": {
        "label": "일본어",
        "prefix": "【仲間はずれ探し】",
        "hooks": {"emoji": "{n}個の{e}の中に1つだけ違うものが！👀",
                  "mirror": "{n}個の{e}の中に1つだけ左右反転が！↔️",
                  "color": "{n}マスの中に1マスだけ色が違う！🎨",
                  "icon": "{n}個のアイコンの中に1つだけ違うものが！👀"},
        "tails": ["レベル3まで見つけられる？", "最後の問題でみんな止まる",
                  "5秒で見つけられる？", "何レベルまで行ける？"],
        "desc": ["5秒で仲間はずれを見つけよう！レベルが上がるほど難しくなります 🔍",
                 "何レベルまで見つけられたかコメントしてね 👇",
                 "毎日新しい問題を公開中。チャンネル登録して毎日挑戦しよう！"],
        "tags": ["#間違い探し", "#仲間はずれ", "#脳トレ", "#クイズ"],
    },
    "es": {
        "label": "스페인어",
        "prefix": "Encuentra el diferente:",
        "hooks": {"emoji": "solo 1 de estos {n} {e} es distinto 👀",
                  "mirror": "solo 1 de estos {n} {e} está invertido ↔️",
                  "color": "solo 1 de estas {n} casillas tiene otro color 🎨",
                  "icon": "solo 1 de estos {n} íconos es distinto 👀"},
        "tails": ["¿Llegas al nivel 3?", "Casi nadie pasa el nivel 3",
                  "Encuéntralo en 5 segundos", "¿Hasta qué nivel llegas?"],
        "desc": ["¡Encuentra el diferente en 5 segundos! Cada nivel es más difícil 🔍",
                 "Comenta hasta qué nivel llegaste 👇",
                 "Un nuevo reto visual cada día. ¡Suscríbete y juega a diario!"],
        "tags": ["#encuentraladiferencia", "#acertijos", "#retovisual", "#juegomental"],
    },
    "pt-BR": {
        "label": "포르투갈어(브라질)",
        "prefix": "Ache o diferente:",
        "hooks": {"emoji": "só 1 destes {n} {e} é diferente 👀",
                  "mirror": "só 1 destes {n} {e} está espelhado ↔️",
                  "color": "só 1 destes {n} quadrados tem outra cor 🎨",
                  "icon": "só 1 destes {n} ícones é diferente 👀"},
        "tails": ["Você chega ao nível 3?", "Quase todo mundo trava no nível 3",
                  "Ache em 5 segundos", "Até que nível você vai?"],
        "desc": ["Ache o diferente em 5 segundos! Cada nível fica mais difícil 🔍",
                 "Comente até que nível você chegou 👇",
                 "Um novo teste de visão todo dia. Inscreva-se e jogue diariamente!"],
        "tags": ["#acheodiferente", "#desafio", "#quiz", "#enigma"],
    },
    "hi": {
        "label": "힌디어",
        "prefix": "अलग वाला ढूंढो:",
        "hooks": {"emoji": "इन {n} {e} में से सिर्फ 1 अलग है 👀",
                  "mirror": "इन {n} {e} में से सिर्फ 1 उल्टा है ↔️",
                  "color": "इन {n} खानों में से सिर्फ 1 का रंग अलग है 🎨",
                  "icon": "इन {n} आइकन में से सिर्फ 1 अलग है 👀"},
        "tails": ["क्या आप लेवल 3 तक पहुंच पाएंगे?", "ज़्यादातर लोग लेवल 3 पर अटक जाते हैं",
                  "5 सेकंड में ढूंढो", "आप कितने लेवल तक जा सकते हैं?"],
        "desc": ["5 सेकंड में अलग वाला ढूंढो! हर लेवल पहले से मुश्किल है 🔍",
                 "कमेंट में बताओ आप किस लेवल तक पहुंचे 👇",
                 "हर दिन एक नया आई टेस्ट। सब्सक्राइब करो और रोज़ खेलो!"],
        "tags": ["#पहेली", "#दिमागीखेल", "#puzzle", "#oddoneout"],
    },
    "id": {
        "label": "인도네시아어",
        "prefix": "Cari yang beda:",
        "hooks": {"emoji": "hanya 1 dari {n} {e} ini yang berbeda 👀",
                  "mirror": "hanya 1 dari {n} {e} ini yang terbalik ↔️",
                  "color": "hanya 1 dari {n} kotak ini yang warnanya beda 🎨",
                  "icon": "hanya 1 dari {n} ikon ini yang berbeda 👀"},
        "tails": ["Bisa sampai level 3?", "Kebanyakan orang gagal di level 3",
                  "Temukan dalam 5 detik", "Kamu bisa sampai level berapa?"],
        "desc": ["Cari yang beda dalam 5 detik! Tiap level makin sulit 🔍",
                 "Tulis di komentar kamu sampai level berapa 👇",
                 "Tes mata baru setiap hari. Subscribe dan main tiap hari!"],
        "tags": ["#cariyangbeda", "#tebakgambar", "#asahotak", "#tesmata"],
    },
}


def ko_font(size):
    for p in KO_FONTS:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


_emoji_font = ImageFont.truetype(EMOJI_FONT, 109)
_emoji_cache = {}

# 날마다 그림 스타일을 바꿔 다른 채널과 같은 화면이 되지 않게 한다.
# noto: Noto Color Emoji(SIL OFL), fluent: Microsoft Fluent Emoji 3D(MIT, assets/fluent)
FLUENT_DIR = ROOT / "assets" / "fluent"
FLUENT = json.loads((FLUENT_DIR / "index.json").read_text())
FLUENT_TOO_SIMILAR = set(json.loads((FLUENT_DIR / "too_similar.json").read_text()))
# 3단계 '아이콘 찾기': Google Material Symbols(Apache 2.0, assets/material)
ICON_FONT = ImageFont.truetype(str(ROOT / "assets" / "material" / "MaterialSymbolsRounded.ttf"), 236)
ICON_FONT.set_variation_by_axes([0, 0, 48, 600])  # 채우기 없음, 기본 그레이드, 큰 글자용 광학 크기, 굵기 600
ICON_CODES = dict(line.split() for line in (ROOT / "assets" / "material" / "MaterialSymbolsRounded.codepoints").read_text().splitlines())
ICON_COLOR = (38, 40, 64)


def style_for(date):
    return "fluent" if datetime.strptime(date, "%Y-%m-%d").toordinal() % 2 else "noto"


def has_style(pair, style):
    if style != "fluent":
        return True
    return all(c in FLUENT for c in pair) and pair not in FLUENT_TOO_SIMILAR


def icon_img(name, size):
    key = ("icon", name, size)
    if key not in _emoji_cache:
        # 아이콘마다 여백을 잘라 내면 '막대 2개'와 '막대 3개'의 크기가 달라지므로, 모든 아이콘을 같은 틀에 그린다
        im = Image.new("RGBA", (240, 240), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((120, 120), chr(int(ICON_CODES[name], 16)), font=ICON_FONT, fill=ICON_COLOR, anchor="mm")
        _emoji_cache[key] = im.resize((size, size), Image.LANCZOS)
    return _emoji_cache[key]


def emoji_img(ch, size, mirror=False, style="noto"):
    key = (ch, size, mirror, style)
    if key not in _emoji_cache:
        if style == "fluent" and ch in FLUENT:
            im = Image.open(FLUENT_DIR / "3d" / FLUENT[ch]).convert("RGBA")
            im.thumbnail((size, size), Image.LANCZOS)
            box = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            box.alpha_composite(im, ((size - im.width) // 2, (size - im.height) // 2))
            im = box
        else:
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
    # 쌍은 순서를 뒤집어 저장되기도 하므로 순서와 상관없이 비교한다
    used = {"".join(sorted(u)) for u in used}
    fresh = [p for p in pool if "".join(sorted(p)) not in used]
    return rng.choice(fresh or pool)


def emoji_chars(pair):
    """쌍에 들어 있는 그림 글자 (모양을 바꾸는 보이지 않는 글자는 뺀다)."""
    return {c for c in pair or "" if c not in "\ufe0f\u200d"}


def category(pair):
    """동물·음식·물건 정도로만 나눈다. 같은 단계에 이틀 연속 동물이 나오지 않게 쓴다."""
    for c in emoji_chars(pair):
        o = ord(c)
        if 0x1F400 <= o <= 0x1F43F or 0x1F980 <= o <= 0x1F9AE or 0x1FAB0 <= o <= 0x1FABF or o == 0x1F577:
            return "animal"
        if 0x1F345 <= o <= 0x1F37F or 0x1F950 <= o <= 0x1F96F or 0x1F9C0 <= o <= 0x1F9CB or 0x1FAD0 <= o <= 0x1FADB:
            return "food"
    return "thing"


def is_face(pair):
    return any(0x1F600 <= ord(c) <= 0x1F64F or c in "☹☺" for c in pair or "")


def pick_answer(rng, n, past):
    """최근 영상의 같은 단계와 정답 자리가 겹쳐 보이지 않게 고른다.
    past: 같은 단계의 최근 정답 (행, 열, 칸 수) 목록, 어제가 맨 앞.
    칸 수가 달라도(7칸, 8칸) 화면에서 같은 자리로 보이므로 화면 비율(0~1)로 비교한다."""
    pos = lambda r, c, k: ((r + 0.5) / k, (c + 0.5) / k)
    prev = [pos(*p) for p in past[:4]]
    cells = [(i // n, i % n) for i in range(n * n)]

    def far(rc, gap, line):
        y, x = pos(*rc, n)
        if any(((y - py) ** 2 + (x - px) ** 2) ** 0.5 < gap for py, px in prev):
            return False
        if prev and (abs(y - prev[0][0]) < line or abs(x - prev[0][1]) < line):  # 어제와 같은 줄·같은 세로줄
            return False
        return True

    for gap, line in ((0.35, 0.15), (0.25, 0.1), (0.15, 0)):
        ok = [rc for rc in cells if far(rc, gap, line)]
        if ok:
            break
    r, c = rng.choice(ok or cells)
    return r * n + c


def build_rounds(rng, used, recent=(), style="noto"):
    """recent: 최근 며칠의 metadata (어제가 맨 앞). 3단계 유형, 얼굴 이모지, 정답 자리가 연달아 겹치지 않게 쓴다."""
    last3 = recent[0]["rounds"][-1] if recent else None
    last_kind = None if last3 is None else ("hard" if last3["kind"] == "emoji" else last3["kind"])
    kind = rng.choice([k for k in ["hard", "mirror", "color", "icon"] if k != last_kind])
    styled = lambda pool: [p for p in pool if has_style(p, style)]
    # 최근 며칠 영상에 나온 그림은 빼서 '어제 본 판다가 또 나오네' 같은 느낌이 들지 않게 한다
    seen = {c for m in recent for r in m["rounds"] if r["kind"] != "icon" for c in emoji_chars(r["pair"])}
    unseen = lambda pool: [p for p in pool if not seen & emoji_chars(p)] or pool

    if kind == "hard":
        pool = styled(HARD)
        if last3 is not None and is_face(last3.get("pair")):  # 어제 3단계가 얼굴이면 오늘은 시계·달 같은 다른 소재
            pool = [p for p in pool if not is_face(p)]
        third = {"kind": "emoji", "pair": pick(rng, unseen(pool), used), "n": 8, "label": "3단계 · 극악"}
    elif kind == "mirror":
        third = {"kind": "mirror", "pair": pick(rng, unseen(styled(MIRROR)), used), "n": 8, "label": "3단계 · 극악"}
    elif kind == "icon":
        third = {"kind": "icon", "pair": pick(rng, ["|".join(p) for p in ICON_PAIRS], used), "n": 8, "label": "3단계 · 극악"}
    else:
        third = {"kind": "color", "pair": None, "n": 7, "label": "3단계 · 극악"}

    taken = (emoji_chars(third["pair"]) if kind != "icon" else set()) | seen
    last1 = recent[0]["rounds"][0] if recent else None
    easy = [p for p in styled(EASY) if not taken & emoji_chars(p)] or styled(EASY)
    if last1 is not None:
        easy = [p for p in easy if category(p) != category(last1["pair"])] or easy
    a = pick(rng, easy, used)
    taken |= emoji_chars(a)  # 한 영상 안에서 같은 그림(🐻🐼 다음 🐨🐼 같은)이 두 번 나오지 않게
    # 2단계는 이틀에 한 번꼴로 '그림체 다른 하나 찾기': 같은 그림인데 하나만 다른 그림체(평면/3D)로 그린다
    last2 = recent[0]["rounds"][1] if recent and len(recent[0]["rounds"]) > 1 else None
    if (last2 is None or last2["kind"] != "art") and rng.random() < 0.5:
        art = [c for c in FLUENT if c not in taken and not is_face(c)]
        second = {"kind": "art", "pair": pick(rng, art, used), "n": 7, "label": "2단계 · 보통"}
    else:
        medium = [p for p in styled(MEDIUM) if not taken & emoji_chars(p)]
        if is_face(third["pair"]):  # 한 영상에 얼굴 문제가 두 번 나오지 않게
            medium = [p for p in medium if not is_face(p)]
        if last2 is not None:
            medium = [p for p in medium if category(p) != category(last2["pair"])] or medium
        second = {"kind": "emoji", "pair": pick(rng, medium or styled(MEDIUM), used), "n": 7, "label": "2단계 · 보통"}
    rounds = [
        {"kind": "emoji", "pair": a, "n": 5, "label": "1단계 · 쉬움"},
        second,
        third,
    ]
    for i, r in enumerate(rounds):
        r["style"] = style
        if rng.random() < 0.5 and r["kind"] == "emoji":
            r["pair"] = r["pair"][::-1] if len(r["pair"]) == 2 else r["pair"]
        past = [(m["rounds"][i]["answer_row"] - 1, m["rounds"][i]["answer_col"] - 1, m["rounds"][i]["grid"])
                for m in recent if len(m["rounds"]) > i]
        r["answer"] = pick_answer(rng, r["n"], past)
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
        r["hue"] = h
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
            im.alpha_composite(emoji_img(r["pair"], size, mirror=is_odd, style=r["style"]), (x, y))
        elif r["kind"] == "art":
            other = "noto" if r["style"] == "fluent" else "fluent"
            im.alpha_composite(emoji_img(r["pair"], size, style=other if is_odd else r["style"]), (x, y))
        elif r["kind"] == "icon":
            a, b = r["pair"].split("|")
            im.alpha_composite(icon_img(b if is_odd else a, size), (x, y))
        else:
            ch = r["pair"][1] if is_odd else r["pair"][0]
            im.alpha_composite(emoji_img(ch, size, style=r["style"]), (x, y))

    cx = GRID_X + (r["answer"] % n + 0.5) * cell
    cy = GRID_Y + (r["answer"] // n + 0.5) * cell
    return im, (cx, cy, cell * 0.62)


# ---------- 프레임 ----------

def background_size(w, h, top, bottom):
    g = np.linspace(0, 1, h)[:, None]
    arr = (np.array(top) * (1 - g) + np.array(bottom) * g)
    arr = np.repeat(arr[:, None, :], w, axis=1).astype(np.uint8)
    return Image.fromarray(arr, "RGB").convert("RGBA")


def background(theme):
    return background_size(W, H, theme[0], theme[1])


def header(base, theme, label):
    d = ImageDraw.Draw(base)
    draw_text(d, (W // 2, 125), CHANNEL, 40, (255, 255, 255, 200), stroke=0)
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


def make_hook_frames(grid, bg, theme):
    base = bg.copy()
    d = ImageDraw.Draw(base)
    draw_text(d, (W // 2, 125), CHANNEL, 40, (255, 255, 255, 200), stroke=0)
    draw_text(d, (W // 2, 250), "이거 찾을 수 있어요?", 92, (255, 255, 255))
    draw_text(d, (W // 2, 380), "마지막 3단계 문제", 58, theme[2], stroke=6)
    d.rounded_rectangle((W // 2 - 210, 455, W // 2 + 210, 545), radius=45, fill=(0, 0, 0, 150))
    draw_text(d, (W // 2, 500), "3단계 · 극악", 50, (255, 255, 255), stroke=0)
    base.alpha_composite(grid, (GRID_X, GRID_Y))
    for f in range(int(HOOK * FPS)):
        im = base.copy()
        d = ImageDraw.Draw(im)
        pulse = 1 + 0.06 * math.sin(f / FPS * 2 * math.pi * 2)
        draw_text(d, (W // 2, GRID_Y + GRID_SIZE + 160), "1단계부터 도전!", int(84 * pulse), (255, 230, 60))
        yield im


def make_outro_frames(bg, theme):
    base = bg.copy()
    d = ImageDraw.Draw(base)
    draw_text(d, (W // 2, 760), "몇 단계까지", 120, (255, 255, 255))
    draw_text(d, (W // 2, 910), "찾았어요?", 120, (255, 255, 255))
    draw_text(d, (W // 2, 1100), "댓글로 알려주세요", 70, theme[2], stroke=6)
    draw_text(d, (W // 2, 1320), f"{CHANNEL} {HANDLE}", 46, (255, 255, 255), stroke=0)
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
    add(tone(523.3, 0.3, 8, 0.3) + tone(784.0, 0.3, 8, 0.2), 0.0)  # 첫 화면 알림음
    t0 = HOOK
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

def recent_meta(date, days=14):
    """지난 영상들의 metadata, 어제가 맨 앞."""
    day = datetime.strptime(date, "%Y-%m-%d")
    out = []
    for k in range(1, days + 1):
        f = OUT_DIR / (day - timedelta(days=k)).strftime("%Y-%m-%d") / "metadata.json"
        if f.exists():
            out.append(json.loads(f.read_text()))
    return out


def recent_titles(date, days=14):
    return {m["title"] for m in recent_meta(date, days)}


def utf16_len(s):
    return len(s.encode("utf-16-le")) // 2


def make_metadata(rng, date, rounds):
    last = rounds[-1]
    if last["kind"] == "color":
        name = next(c for limit, c in COLOR_NAMES if last["hue"] < limit)
    elif last["kind"] == "icon":
        name = ICON_NAMES.get(last["pair"].split("|")[0], "그림")
    else:
        name = NAMES.get(last["pair"][0], "그림")
    hook = "【다른 하나 찾기】 " + HOOKS[last["kind"]].strip().format(
        name=name, n=last["n"] ** 2, e="" if last["kind"] == "icon" else (last["pair"] or "")[:1])
    # 최근 영상과 제목이 똑같으면 '찍어 낸 영상'처럼 보이므로 겹치지 않는 꼬리말을 고른다
    seen = recent_titles(date)
    tails = [t for t in TAILS if f"{hook} | {t} #shorts"[:100] not in seen]
    title = f"{hook} | {rng.choice(tails or TAILS)}"
    desc = "\n".join([
        "5초 안에 다른 하나를 찾아보세요! 단계가 올라갈수록 어려워집니다 🔍",
        "몇 단계까지 찾았는지 댓글로 남겨주세요 👇",
        f"{CHANNEL}에서 매일 새로운 눈썰미 테스트가 올라옵니다. 구독하고 매일 도전하세요!",
        "",
        "Find the odd one out in 5 seconds! How far can you get?",
        "",
        " ".join(HASHTAGS),
    ])
    e = (last["pair"] or "")[:1] if last["kind"] in ("emoji", "mirror") else ""
    tail_i = rng.randrange(4)  # 언어마다 같은 꼬리말을 써서 뜻을 맞춘다
    localizations = {}
    for lang, L in LOCALES.items():
        hook_l = L["hooks"][last["kind"]].format(n=last["n"] ** 2, e=e)
        # 유튜브는 이모지를 두 글자로 셀 수 있어서 여유 있게 90자 안으로 맞춘다
        tails = [L["tails"][tail_i]] + sorted(L["tails"], key=len)
        title_l = next((t for t in (f"{L['prefix']} {hook_l} | {tail} #shorts" for tail in tails)
                        if utf16_len(t) <= 90), f"{L['prefix']} {hook_l} #shorts")
        localizations[lang] = {
            "title": title_l,
            "description": "\n".join(L["desc"] + ["", " ".join(["#shorts"] + L["tags"])]),
        }
    return {
        "date": date,
        "title": f"{title} #shorts"[:100],
        "description": desc,
        "defaultLanguage": "ko",
        "localizations": localizations,
        "tags": [h.lstrip("#") for h in HASHTAGS] + ["눈썰미", "숨은그림찾기", "odd one out"],
        "categoryId": "24",  # Entertainment
        "madeForKids": False,
        "containsSyntheticMedia": False,  # 실사처럼 보이는 합성물이 아니라 표시 대상 아님
        "style": rounds[0]["style"],
        "rounds": [{"kind": r["kind"], "pair": r["pair"], "grid": r["n"],
                    "answer_row": r["answer"] // r["n"] + 1, "answer_col": r["answer"] % r["n"] + 1}
                   for r in rounds],
    }


def main():
    ap = argparse.ArgumentParser()
    kst_today = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d")
    ap.add_argument("--date", default=kst_today)
    ap.add_argument("--force", action="store_true", help="이미 올린 날짜도 다시 만든다 (올린 영상은 그대로)")
    args = ap.parse_args()

    # 올린 기록(videoId)을 덮어쓰면 자동 업로드가 같은 날 영상을 또 올린다
    old_meta = OUT_DIR / args.date / "metadata.json"
    uploaded = {k: v for k, v in json.loads(old_meta.read_text()).items()
                if k in ("videoId", "publishAt", "uploadedBy")} if old_meta.exists() else {}
    if uploaded.get("videoId") and not args.force:
        raise SystemExit(f"{args.date} 영상은 이미 올렸습니다 ({uploaded['videoId']}). 다시 만들려면 --force")

    rng = random.Random(f"nunsseulmi-{args.date}")
    history = json.loads(HISTORY.read_text()) if HISTORY.exists() else {}
    used = {p for d, ps in history.items() if d != args.date for p in ps}

    rounds = build_rounds(rng, used, recent_meta(args.date, days=4), style_for(args.date))
    # 날짜 순서대로 돌려서 연속된 이틀이 같은 색이 되지 않게 한다
    theme = THEMES[datetime.strptime(args.date, "%Y-%m-%d").toordinal() % len(THEMES)]
    bg = background(theme)

    out = OUT_DIR / args.date
    out.mkdir(parents=True, exist_ok=True)
    total = HOOK + len(rounds) * (ROUND_SHOW + ROUND_REVEAL) + OUTRO
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

    # 첫 화면에 3단계 그리드가 필요하므로 그리드를 먼저 모두 그린다 (rng 사용 순서는 그대로)
    grids = [render_grid(r, rng) for r in rounds]
    for k, frame in enumerate(make_hook_frames(grids[-1][0], bg, theme)):
        if k == 0:  # 표지: 유튜브가 정답 장면을 표지로 고르지 않게 첫 화면을 따로 저장한다
            frame.convert("RGB").save(out / "cover.jpg", quality=90)
        proc.stdin.write(frame.convert("RGB").tobytes())

    preview = None
    for r, (grid, ans) in zip(rounds, grids):
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

    meta = make_metadata(rng, args.date, rounds) | uploaded
    (out / "metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    # 손 업로드 기간에 스튜디오에 붙여 넣기 쉬운 형태
    lines = [f"{args.date[5:].replace('-', '/')} 쇼츠 · 언어별 제목과 설명",
             "업로드를 마친 뒤 스튜디오 왼쪽 '자막' → 이 영상 → 언어 추가 → 그 줄의 '제목 및 설명' 칸 '추가'"
             "(옆 '자막' 칸 말고) → 붙여 넣고 '게시'", ""]
    for lang, loc in meta["localizations"].items():
        lines += [f"■ {LOCALES[lang]['label']} ({lang})", "[제목]", loc["title"], "[설명]", loc["description"], ""]
    (out / "translations.txt").write_text("\n".join(lines))
    history[args.date] = [r["pair"] for r in rounds if r["pair"]]
    HISTORY.write_text(json.dumps(dict(sorted(history.items())), ensure_ascii=False, indent=1))
    print(f"완료: {mp4} ({total:.1f}초)  제목: {meta['title']}")


if __name__ == "__main__":
    main()
