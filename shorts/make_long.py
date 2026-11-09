"""'다른 하나 찾기 쉬움부터 극악까지 40문제' 가로 긴 영상(약 10분)을 만든다.

쇼츠는 수익 창출 시청시간에 들어가지 않으므로, 긴 영상으로 시청시간을 쌓는다(experiments.md 실험 3).
TV로 보는 중장년 시청자를 생각해 가로 화면, 큰 글씨, 문제마다 넉넉한 시간을 준다.
그림 소재와 그리는 방법은 make_short.py의 것을 그대로 쓴다.

사용법:
    python3 shorts/make_long.py --date 2026-10-31          # shorts/output_long/<날짜>/
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
from PIL import Image, ImageDraw

import make_short as ms
from emoji_pool import EASY, HARD, ICON_PAIRS, MEDIUM, MIRROR

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "output_long"
HISTORY = ROOT / "history_long.json"

W, H, FPS = 1920, 1080, 24
REVEAL = 3.0  # 정답 3초 (문제 시간은 단계마다 LEVELS에)
INTRO, LEVEL_CARD, OUTRO = 8.0, 3.0, 12.0
PER_LEVEL = 10
GRID_X, GRID_Y = 960, 110  # 그리드 왼쪽 위 (크기는 make_short.GRID_SIZE = 860)
PANEL_X = 480  # 왼쪽 정보 칸의 가운데

# 11/2 주간 결정: 30문제 모두 극악(10/27) → 쉬움부터 극악까지 40문제로 바꾼다.
# 비슷한 긴 영상 상위 25편 중 전부 극악인 영상은 없었고, 거의 다 쉬움 → 극악 순서였다(research/2026-10-30.md 5절).
# 앞이 쉬워야 '나도 되네' 하고 남고, 뒤로 갈수록 어려워져야 끝까지 본다. 쉬운 단계는 시간도 짧게 준다.
LEVELS = [  # (이름, 칸 수, 배경 테마 번호, 문제 시간(초), 유형 목록)
    ("1단계 쉬움 · 36칸", 6, 3, 8.0, ["easy"]),
    ("2단계 보통 · 49칸", 7, 4, 10.0, ["medium", "art"]),
    ("3단계 어려움 · 64칸", 8, 1, 12.0, ["hard", "icon", "mirror", "color"]),
    ("4단계 극악 · 100칸", 10, 0, 15.0, ["hard", "icon", "mirror", "art", "color"]),
]


def norm(p):
    return "".join(sorted(p))


def build_questions(rng, used):
    """40문제. 한 영상 안에서 같은 그림이 두 번 나오지 않고, 그림체(평면/3D)와 유형을 섞는다."""
    taken = set()
    parts = lambda p: set(p.split("|")) if "|" in p else set(p)  # 아이콘 쌍은 'lock|lock_open' 형태

    def take(pool, style):
        ok = lambda p: ("|" in p or ms.has_style(p, style)) and not taken & parts(p)
        cands = [p for p in pool if ok(p) and norm(p) not in used] or [p for p in pool if ok(p)]
        p = rng.choice(cands)
        taken.update(parts(p))
        return p

    qs = []
    art_pool = [c for c in ms.FLUENT if not ms.is_face(c)]
    for level, (label, n, _, show, kinds) in enumerate(LEVELS):
        for i in range(PER_LEVEL):
            k = level * PER_LEVEL + i
            style = "fluent" if k % 2 else "noto"
            kind = kinds[(k + level) % len(kinds)]  # 단계가 바뀌어도 같은 순서로 반복되지 않게 한 칸씩 민다
            if kind == "easy":
                q = {"kind": "emoji", "pair": take(EASY, style)}
            elif kind == "medium":
                q = {"kind": "emoji", "pair": take(MEDIUM, style)}
            elif kind == "hard":
                q = {"kind": "emoji", "pair": take(HARD, style)}
            elif kind == "icon":
                q = {"kind": "icon", "pair": take(["|".join(p) for p in ICON_PAIRS], style)}
            elif kind == "mirror":
                q = {"kind": "mirror", "pair": take(MIRROR, style)}
            elif kind == "art":
                q = {"kind": "art", "pair": take(art_pool, style)}
            else:
                q = {"kind": "color", "pair": None}
            q.update(n=n, style=style, level=level, show=show)
            if q["kind"] == "emoji" and rng.random() < 0.5:
                q["pair"] = q["pair"][::-1]
            qs.append(q)
    # 정답 자리는 앞 문제들과 화면에서 겹치지 않게 (같은 단계의 직전 4문제 기준)
    for i, q in enumerate(qs):
        past = [(p["answer"] // p["n"], p["answer"] % p["n"], p["n"]) for p in reversed(qs[max(0, i - 4):i])]
        q["answer"] = ms.pick_answer(rng, q["n"], past)
    return qs


# ---------- 프레임 ----------

def background(level):
    return ms.background_size(W, H, *ms.THEMES[LEVELS[level][2]][:2])


def accent(level):
    return ms.THEMES[LEVELS[level][2]][2]


def panel(base, level, number):
    d = ImageDraw.Draw(base)
    ms.draw_text(d, (PANEL_X, 140), ms.CHANNEL, 44, (255, 255, 255, 210), stroke=0)
    ms.draw_text(d, (PANEL_X, 270), "다른 하나를 찾아라!", 76, (255, 255, 255))
    d.rounded_rectangle((PANEL_X - 200, 360, PANEL_X + 200, 440), radius=40, fill=(0, 0, 0, 150))
    ms.draw_text(d, (PANEL_X, 400), LEVELS[level][0], 44, (255, 255, 255), stroke=0)
    ms.draw_text(d, (PANEL_X, 540), f"{number} / {len(LEVELS) * PER_LEVEL}", 96, accent(level))
    ms.draw_text(d, (PANEL_X, 625), "문제", 44, (255, 255, 255, 220), stroke=0)


def question_frames(q, number, grid, ans):
    base = background(q["level"])
    panel(base, q["level"], number)
    base.alpha_composite(grid, (GRID_X, GRID_Y))
    bar_y, bar_w = 760, 560
    show = q["show"]
    for f in range(int(show * FPS)):
        t = f / FPS
        im = base.copy()
        d = ImageDraw.Draw(im)
        frac = 1 - t / show
        x0 = PANEL_X - bar_w // 2
        d.rounded_rectangle((x0, bar_y, x0 + bar_w, bar_y + 34), radius=17, fill=(0, 0, 0, 120))
        if frac > 0:
            col = accent(q["level"]) if frac > 0.3 else (255, 70, 70)
            d.rounded_rectangle((x0, bar_y, x0 + max(34, int(bar_w * frac)), bar_y + 34), radius=17, fill=col)
        sec = math.ceil(show - t)
        pop = 1 + 0.2 * max(0, 1 - (t % 1) * 4) if sec <= 5 else 1
        ms.draw_text(d, (PANEL_X, bar_y + 150), str(sec), int(120 * pop), (255, 255, 255))
        yield im

    cx, cy, rad = ans
    reveal = base.copy()
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shade)
    gs = ms.GRID_SIZE
    sd.rectangle((GRID_X, GRID_Y, GRID_X + gs, GRID_Y + gs), fill=(0, 0, 0, 140))
    sd.ellipse((cx - rad, cy - rad, cx + rad, cy + rad), fill=(0, 0, 0, 0))
    reveal.alpha_composite(shade)
    row, col = q["answer"] // q["n"] + 1, q["answer"] % q["n"] + 1
    for f in range(int(REVEAL * FPS)):
        im = reveal.copy()
        d = ImageDraw.Draw(im)
        grow = min(1, f / 6)
        rr = rad * (1.6 - 0.6 * grow)
        d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=(255, 40, 40), width=12)
        ms.draw_text(d, (PANEL_X, bar_y + 60), "정답!", 110, (255, 230, 60))
        ms.draw_text(d, (PANEL_X, bar_y + 190), f"{row}번째 줄 · {col}번째 칸", 48, (255, 255, 255), stroke=0)
        yield im


def card_frames(level, lines, seconds):
    base = background(level)
    d = ImageDraw.Draw(base)
    y = H // 2 - (len(lines) - 1) * 70
    for text, size, color in lines:
        ms.draw_text(d, (W // 2, y), text, size, color)
        y += 140
    for _ in range(int(seconds * FPS)):
        yield base


def intro_frames():
    return card_frames(0, [
        ("다른 하나 찾기 40문제", 104, (255, 255, 255)),
        ("쉬움 → 보통 → 어려움 → 극악, 갈수록 어려워져요", 60, accent(0)),
        ("끝까지 다 찾으면 상위 1% 눈썰미!", 64, (255, 255, 255)),
    ], INTRO)


def level_frames(level):
    tips = ["몸풀기! 한 문제에 8초씩", "조금 어려워져요 · 10초씩", "이제 64개 중 하나 · 12초씩",
            "마지막! 100개 중 하나 · 15초씩"]
    return card_frames(level, [
        (LEVELS[level][0] + " 시작!", 110, (255, 255, 255)),
        (tips[level], 56, accent(level)),
    ], LEVEL_CARD)


def outro_frames():
    return card_frames(len(LEVELS) - 1, [
        ("몇 문제 찾으셨나요?", 110, (255, 255, 255)),
        ("댓글로 점수를 남겨 주세요", 64, accent(len(LEVELS) - 1)),
        (f"{ms.CHANNEL} {ms.HANDLE} · 매일 새 문제", 48, (255, 255, 255)),
    ], OUTRO)


# ---------- 소리 ----------

def make_audio(timeline, total, path):
    """timeline: (시작 시각, 종류, 문제 시간) 목록. 종류는 'question' 또는 'card'."""
    a = np.zeros(int(ms.SR * total) + ms.SR)

    def add(sig, at):
        i = int(at * ms.SR)
        a[i:i + len(sig)] += sig[: len(a) - i]

    notes = [261.6, 329.6, 392.0, 523.3, 392.0, 329.6]
    beat = 0.5  # 긴 영상은 배경음을 느리고 잔잔하게
    for k in range(int(total / beat)):
        add(ms.tone(notes[k % len(notes)], 0.6, 4, 0.04), k * beat)
    for at, kind, show in timeline:
        if kind == "question":
            for s in range(int(show) - 5, int(show)):  # 마지막 5초만 째깍
                add(ms.tone(1500 if s == int(show) - 1 else 1000, 0.08, 40, 0.25), at + s)
            add(ms.tone(880, 0.8, 5, 0.3) + ms.tone(1320, 0.8, 6, 0.18), at + show)
        else:
            add(ms.tone(523.3, 0.4, 6, 0.25) + ms.tone(784.0, 0.4, 6, 0.18), at)
    a = np.clip(a, -1, 1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(ms.SR)
        w.writeframes((a * 32767).astype(np.int16).tobytes())


# ---------- 메타데이터 ----------

def stamp(sec):
    return f"{int(sec) // 60}:{int(sec) % 60:02d}"


def make_metadata(date, number, questions, chapters):
    # 영어를 함께 적는다: 작은 채널 긴 영상 중 1,000회를 넘긴 것은 영어를 섞은 제목뿐이었다(research/2026-10-31.md)
    title = f"【다른 하나 찾기/치매예방】 쉬움→극악 40문제, 다 찾으면 상위 1%! | Find the Odd One Out #{number}"
    lines = [
        "숨어 있는 '다른 하나'를 찾아보세요! 쉬움 10문제로 몸을 풀고 보통, 어려움을 지나 마지막 극악 100칸까지 40문제입니다. 뒤로 갈수록 시간도 8초에서 15초로 늘어나요.",
        "그림 모양, 그림체(평면/3D), 아이콘, 색깔, 좌우 반전까지 매 문제가 다릅니다.",
        "몇 문제 찾으셨는지 댓글로 남겨 주세요 👇",
        "",
        *[f"{stamp(t)} {name}" for t, name in chapters],
        "",
        f"{ms.CHANNEL}에서 매일 새로운 눈썰미 테스트가 올라옵니다. 구독하고 매일 두뇌 운동하세요!",
        "",
        "Find the odd one out! 40 puzzles from Easy to Impossible, 36 to 100 tiles. How many can you find?",
        "",
        "#다른그림찾기 #틀린그림찾기 #치매예방 #두뇌운동 #집중력 #눈썰미테스트 #spotthedifference #findtheoddoneout",
    ]
    return {
        "date": date,
        "number": number,
        "title": title[:100],
        "description": "\n".join(lines),
        "tags": ["다른그림찾기", "틀린그림찾기", "치매예방", "두뇌운동", "집중력", "눈썰미", "눈썰미테스트",
                 "다른 하나 찾기", "spot the difference", "find the odd one out", "brain test", "puzzle"],
        "categoryId": "24",
        "madeForKids": False,
        "containsSyntheticMedia": False,
        "questions": [{"kind": q["kind"], "pair": q["pair"], "style": q["style"], "grid": q["n"],
                       "answer_row": q["answer"] // q["n"] + 1, "answer_col": q["answer"] % q["n"] + 1}
                      for q in questions],
    }


def make_thumbnail(path, grid, level):
    """1280x720 미리보기 이미지: 큰 글씨 + 어려움 문제 그리드 (정답 표시 없음)."""
    im = ms.background_size(1280, 720, *ms.THEMES[LEVELS[level][2]][:2])
    g = grid.resize((560, 560), Image.LANCZOS)
    im.alpha_composite(g, (680, 80))
    d = ImageDraw.Draw(im)
    ms.draw_text(d, (340, 190), "다른 하나", 110, (255, 255, 255))
    ms.draw_text(d, (340, 320), "40문제", 104, accent(level))
    ms.draw_text(d, (340, 470), "쉬움 → 극악", 72, (255, 255, 255))
    ms.draw_text(d, (340, 570), "상위 1% 눈썰미!", 72, (255, 230, 60))
    im.convert("RGB").save(path, quality=92)


def main():
    ap = argparse.ArgumentParser()
    kst_today = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d")
    ap.add_argument("--date", default=kst_today)
    args = ap.parse_args()

    # 11/9 주간 결정: 긴 영상 두 편이 조회 1~2회 → 구독자가 늘 때까지 격주로. 최근 13일 안에 올린 긴 영상이 있으면 건너뛴다
    target = datetime.strptime(args.date, "%Y-%m-%d")
    for m in OUT_DIR.glob("*/metadata.json"):
        d = datetime.strptime(m.parent.name, "%Y-%m-%d")
        if m.parent.name != args.date and json.loads(m.read_text()).get("videoId") and 0 < (target - d).days < 14:
            raise SystemExit(f"{m.parent.name} 긴 영상을 올린 지 14일이 안 돼 건너뜁니다(격주)")
    rng = random.Random(f"nunsseulmi-long-{args.date}")
    history = json.loads(HISTORY.read_text()) if HISTORY.exists() else {}
    used = {norm(p) for d, ps in history.items() if d != args.date for p in ps}
    number = len([d for d in history if d != args.date]) + 1

    questions = build_questions(rng, used)
    grids = []
    for q in questions:
        grid, (cx, cy, rad) = ms.render_grid(q, rng)
        # render_grid는 쇼츠 화면 기준 좌표를 주므로 긴 영상의 그리드 위치로 옮긴다
        grids.append((grid, (cx - ms.GRID_X + GRID_X, cy - ms.GRID_Y + GRID_Y, rad)))

    out = OUT_DIR / args.date
    out.mkdir(parents=True, exist_ok=True)

    # 순서: 인트로 → (단계 카드 → 10문제) x 3 → 아웃트로
    timeline, chapters, t = [(0.0, "card", 0)], [(0.0, "시작")], INTRO
    for level in range(len(LEVELS)):
        chapters.append((t, LEVELS[level][0]))
        timeline.append((t, "card", 0))
        t += LEVEL_CARD
        show = LEVELS[level][3]
        for _ in range(PER_LEVEL):
            timeline.append((t, "question", show))
            t += show + REVEAL
    chapters.append((t, "마무리"))
    timeline.append((t, "card", 0))
    total = t + OUTRO

    wav = out / "audio.wav"
    make_audio(timeline, total, wav)
    mp4 = out / "long.mp4"
    proc = subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", str(wav),
        "-c:v", "libx264", "-preset", "medium", "-crf", "22", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", str(mp4),
    ], stdin=subprocess.PIPE)

    def write(frames):
        for f in frames:
            proc.stdin.write(f.convert("RGB").tobytes())

    write(intro_frames())
    for level in range(len(LEVELS)):
        write(level_frames(level))
        for i in range(PER_LEVEL):
            k = level * PER_LEVEL + i
            write(question_frames(questions[k], k + 1, *grids[k]))
    write(outro_frames())
    proc.stdin.close()
    if proc.wait() != 0:
        raise SystemExit("ffmpeg 인코딩 실패")
    wav.unlink()

    make_thumbnail(out / "thumbnail.jpg", grids[-1][0], len(LEVELS) - 1)
    meta = make_metadata(args.date, number, questions, chapters)
    (out / "metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    history[args.date] = [q["pair"] for q in questions if q["pair"]]
    HISTORY.write_text(json.dumps(dict(sorted(history.items())), ensure_ascii=False, indent=1))
    print(f"완료: {mp4} ({total / 60:.1f}분)  제목: {meta['title']}")


if __name__ == "__main__":
    main()
