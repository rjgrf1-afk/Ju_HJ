"""'다른 하나 찾기 극악 30문제' 가로 긴 영상(약 10분)을 만든다.

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
SHOW, REVEAL = 15.0, 3.0  # 문제당 15초 + 정답 3초
INTRO, LEVEL_CARD, OUTRO = 8.0, 3.0, 12.0
PER_LEVEL = 10
GRID_X, GRID_Y = 960, 110  # 그리드 왼쪽 위 (크기는 make_short.GRID_SIZE = 860)
PANEL_X = 480  # 왼쪽 정보 칸의 가운데

# 쉬운 문제로 시작하면 지루해 이탈하므로(채널 주인 의견 10/27) 30문제 모두 극악으로 내고,
# 뒤로 갈수록 칸 수를 늘려 끝까지 긴장감을 유지한다
LEVELS = [  # (이름, 칸 수, 배경 테마 번호)
    ("극악 1 · 64칸", 8, 4),
    ("극악 2 · 81칸", 9, 1),
    ("극악 3 · 100칸", 10, 0),
]
KINDS = ["hard", "icon", "mirror", "art", "color"]  # 문제마다 유형을 돌린다


def norm(p):
    return "".join(sorted(p))


def build_questions(rng, used):
    """30문제. 한 영상 안에서 같은 그림이 두 번 나오지 않고, 그림체(평면/3D)와 유형을 섞는다."""
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
    for level, (label, n, _) in enumerate(LEVELS):
        for i in range(PER_LEVEL):
            k = level * PER_LEVEL + i
            style = "fluent" if k % 2 else "noto"
            kind = KINDS[(k + level) % len(KINDS)]  # 단계가 바뀌어도 같은 순서로 반복되지 않게 한 칸씩 민다
            if kind == "hard":
                q = {"kind": "emoji", "pair": take(HARD, style)}
            elif kind == "icon":
                q = {"kind": "icon", "pair": take(["|".join(p) for p in ICON_PAIRS], style)}
            elif kind == "mirror":
                q = {"kind": "mirror", "pair": take(MIRROR, style)}
            elif kind == "art":
                q = {"kind": "art", "pair": take(art_pool, style)}
            else:
                q = {"kind": "color", "pair": None}
            q.update(n=n, style=style, level=level)
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
    for f in range(int(SHOW * FPS)):
        t = f / FPS
        im = base.copy()
        d = ImageDraw.Draw(im)
        frac = 1 - t / SHOW
        x0 = PANEL_X - bar_w // 2
        d.rounded_rectangle((x0, bar_y, x0 + bar_w, bar_y + 34), radius=17, fill=(0, 0, 0, 120))
        if frac > 0:
            col = accent(q["level"]) if frac > 0.3 else (255, 70, 70)
            d.rounded_rectangle((x0, bar_y, x0 + max(34, int(bar_w * frac)), bar_y + 34), radius=17, fill=col)
        sec = math.ceil(SHOW - t)
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
        ("다른 하나 찾기 극악 30문제", 104, (255, 255, 255)),
        ("64칸 → 81칸 → 100칸, 갈수록 어려워져요", 60, accent(0)),
        ("끝까지 다 찾으면 상위 1% 눈썰미!", 64, (255, 255, 255)),
    ], INTRO)


def level_frames(level):
    tips = ["한 문제에 15초씩 드려요", "이제 81개 중 하나예요", "마지막! 100개 중 하나를 찾아보세요"]
    return card_frames(level, [
        (LEVELS[level][0] + " 시작!", 110, (255, 255, 255)),
        (tips[level], 56, accent(level)),
    ], LEVEL_CARD)


def outro_frames():
    return card_frames(2, [
        ("몇 문제 찾으셨나요?", 110, (255, 255, 255)),
        ("댓글로 점수를 남겨 주세요", 64, accent(2)),
        (f"{ms.CHANNEL} {ms.HANDLE} · 매일 새 문제", 48, (255, 255, 255)),
    ], OUTRO)


# ---------- 소리 ----------

def make_audio(timeline, total, path):
    """timeline: (시작 시각, 종류) 목록. 종류는 'question' 또는 'card'."""
    a = np.zeros(int(ms.SR * total) + ms.SR)

    def add(sig, at):
        i = int(at * ms.SR)
        a[i:i + len(sig)] += sig[: len(a) - i]

    notes = [261.6, 329.6, 392.0, 523.3, 392.0, 329.6]
    beat = 0.5  # 긴 영상은 배경음을 느리고 잔잔하게
    for k in range(int(total / beat)):
        add(ms.tone(notes[k % len(notes)], 0.6, 4, 0.04), k * beat)
    for at, kind in timeline:
        if kind == "question":
            for s in range(int(SHOW) - 5, int(SHOW)):  # 마지막 5초만 째깍
                add(ms.tone(1500 if s == int(SHOW) - 1 else 1000, 0.08, 40, 0.25), at + s)
            add(ms.tone(880, 0.8, 5, 0.3) + ms.tone(1320, 0.8, 6, 0.18), at + SHOW)
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
    title = f"【다른 하나 찾기/치매예방】 극악 30문제, 다 찾으면 상위 1% 눈썰미! | 눈썰미 연구소 #{number}"
    lines = [
        "숨어 있는 '다른 하나'를 찾아보세요! 30문제 모두 극악, 64칸에서 시작해 81칸, 100칸으로 갈수록 어려워집니다. 한 문제에 15초씩 드려요.",
        "그림 모양, 그림체(평면/3D), 아이콘, 색깔, 좌우 반전까지 매 문제가 다릅니다.",
        "몇 문제 찾으셨는지 댓글로 남겨 주세요 👇",
        "",
        *[f"{stamp(t)} {name}" for t, name in chapters],
        "",
        f"{ms.CHANNEL}에서 매일 새로운 눈썰미 테스트가 올라옵니다. 구독하고 매일 두뇌 운동하세요!",
        "",
        "Find the odd one out! 30 extreme puzzles, from 64 to 100 tiles. How many can you find?",
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
    ms.draw_text(d, (340, 320), "극악 30문제", 104, accent(level))
    ms.draw_text(d, (340, 470), "다 찾으면", 72, (255, 255, 255))
    ms.draw_text(d, (340, 570), "상위 1% 눈썰미!", 72, (255, 230, 60))
    im.convert("RGB").save(path, quality=92)


def main():
    ap = argparse.ArgumentParser()
    kst_today = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d")
    ap.add_argument("--date", default=kst_today)
    args = ap.parse_args()

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
    timeline, chapters, t = [(0.0, "card")], [(0.0, "시작")], INTRO
    for level in range(len(LEVELS)):
        chapters.append((t, LEVELS[level][0]))
        timeline.append((t, "card"))
        t += LEVEL_CARD
        for _ in range(PER_LEVEL):
            timeline.append((t, "question"))
            t += SHOW + REVEAL
    chapters.append((t, "마무리"))
    timeline.append((t, "card"))
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

    make_thumbnail(out / "thumbnail.jpg", grids[-1][0], 2)
    meta = make_metadata(args.date, number, questions, chapters)
    (out / "metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    history[args.date] = [q["pair"] for q in questions if q["pair"]]
    HISTORY.write_text(json.dumps(dict(sorted(history.items())), ensure_ascii=False, indent=1))
    print(f"완료: {mp4} ({total / 60:.1f}분)  제목: {meta['title']}")


if __name__ == "__main__":
    main()
