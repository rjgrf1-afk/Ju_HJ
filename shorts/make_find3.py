"""저녁 쇼츠 두 번째 형식: '다른 3개 다 찾기' (6주차 결정, 11/23부터 하루걸러).

저녁 3단계가 매일 같은 틀(25.6초)이라 11/19~11/21 사흘 연속 첫 노출에서 막혔다(research/2026-11-20~22.md).
잘되는 단계형 채널(Sharp Eye Test)은 편마다 틀을 바꾸고 '여러 개 다 찾기'를 주력으로 쓴다.
판 하나(8x8)에 다른 그림 3개를 숨기고 12초 → 정답 3개 공개 → 보너스 퀴즈 → 아웃트로 (약 21초).
make_short.py가 FIND3 날에 이 모듈을 부른다. 그림 고르기·겹침 피하기는 make_short.build_rounds의 3단계를 그대로 쓴다.
"""
import json
import math
import subprocess
import wave

import numpy as np
from PIL import Image, ImageDraw

import make_short as S

SHOW, REVEAL = 12.0, 3.0
LABEL = "3개 찾기 · 극악"
HOOKS = {
    "emoji": "{name} {n}개 중 다른 3개를 모두 찾아보세요 {e}",
    "mirror": "{name} {n}개 중 뒤집힌 3개를 모두 찾아보세요 {e}",
    "color": "{name} {n}개 중 색이 다른 3개를 찾아보세요 🎨",
    "icon": "{name} {n}개 중 다른 3개를 모두 찾아보세요 👀",
}
TAILS = ["3개 다 찾으면 상위 1%", "마지막 하나가 안 보여요", "몇 개 찾았나요?", "12초 안에 전부 찾기"]
LOC = {  # (앞머리, 문구, 꼬리말들, 설명)
    "en": ("Find the 3 Odd Ones:", "3 of these {n} are different {e}", ["Can you find all 3?", "Only 1% find the last one"],
           ["Find all 3 odd ones in 12 seconds! 🔍", "Comment the 3 cells (e.g. B2 E5 G7) 👇", "New puzzles every day. Subscribe and play daily!"],
           ["#shorts", "#oddoneout", "#findthedifference", "#brainteaser"]),
    "ja": ("【仲間はずれ3つ探し】", "{n}個の中に違うものが3つ{e}", ["全部見つけられる？", "最後の1つが見つからない"],
           ["12秒で仲間はずれを3つ全部見つけよう！🔍", "答えのマス3つをコメントしてね（例: B2 E5 G7）👇", "毎日新しい問題を公開中！"],
           ["#shorts", "#間違い探し", "#脳トレ", "#認知症予防"]),
    "es": ("Encuentra los 3 diferentes:", "3 de estos {n} son distintos {e}", ["¿Encuentras los 3?", "El último casi nadie lo ve"],
           ["¡Encuentra los 3 diferentes en 12 segundos! 🔍", "Comenta las 3 casillas (ej.: B2 E5 G7) 👇", "¡Un nuevo reto cada día!"],
           ["#shorts", "#encuentraladiferencia", "#retovisual"]),
    "pt-BR": ("Ache os 3 diferentes:", "3 destes {n} são diferentes {e}", ["Você acha os 3?", "O último quase ninguém vê"],
              ["Ache os 3 diferentes em 12 segundos! 🔍", "Comente as 3 casas (ex.: B2 E5 G7) 👇", "Um novo desafio todo dia!"],
              ["#shorts", "#testedevisao", "#desafio"]),
    "hi": ("Find the 3 Odd Ones:", "3 of these {n} are different {e}", ["Can you find all 3?", "Only 1% find the last one"],
           ["12 सेकंड में तीनों अलग वाले ढूंढो! 🔍", "तीनों खाने कमेंट करें (जैसे B2 E5 G7) 👇", "हर दिन नया चैलेंज!"],
           ["#shorts", "#oddoneout", "#braintest"]),
    "id": ("Cari 3 yang beda:", "3 dari {n} ini berbeda {e}", ["Bisa temukan semuanya?", "Yang terakhir susah dicari"],
           ["Temukan 3 yang beda dalam 12 detik! 🔍", "Tulis 3 kotaknya di komentar (mis. B2 E5 G7) 👇", "Tantangan baru setiap hari!"],
           ["#shorts", "#tesmata", "#asahotak"]),
}


def pick_three(rng, n, past):
    first = S.pick_answer(rng, n, past)
    ans = [first]
    while len(ans) < 3:
        sib = [(a // n, a % n, n) for a in ans]
        a = S.pick_answer(rng, n, [], sib)
        if a not in ans:
            ans.append(a)
    return ans


def header3(base, theme, label):
    d = ImageDraw.Draw(base)
    S.draw_text(d, (S.W // 2, 125), S.CHANNEL, 40, (255, 255, 255, 200), stroke=0)
    S.draw_text(d, (S.W // 2, 230), "다른 3개를 찾아라!", 92, (255, 255, 255))
    S.draw_text(d, (S.W // 2, 360), "3개 다 찾으면 상위 1%", 58, theme[2], stroke=6)
    d.rounded_rectangle((S.W // 2 - 210, 455, S.W // 2 + 210, 545), radius=45, fill=(0, 0, 0, 150))
    S.draw_text(d, (S.W // 2, 500), label, 50, (255, 255, 255), stroke=0)


def puzzle_frames(r, grid, bg, theme):
    base = bg.copy()
    header3(base, theme, LABEL)
    base.alpha_composite(grid, (S.GRID_X, S.GRID_Y))
    S.draw_grid_labels(ImageDraw.Draw(base), r["n"])
    bar_y = S.GRID_Y + S.GRID_SIZE + 70
    for f in range(int(SHOW * S.FPS)):
        t = f / S.FPS
        im = base.copy()
        d = ImageDraw.Draw(im)
        frac = 1 - t / SHOW
        d.rounded_rectangle((S.GRID_X, bar_y, S.GRID_X + S.GRID_SIZE, bar_y + 36), radius=18, fill=(0, 0, 0, 120))
        if frac > 0:
            col = theme[2] if frac > 0.3 else (255, 70, 70)
            d.rounded_rectangle((S.GRID_X, bar_y, S.GRID_X + max(36, int(S.GRID_SIZE * frac)), bar_y + 36), radius=18, fill=col)
        sec = math.ceil(SHOW - t)
        pop = 1 + 0.25 * max(0, 1 - (t % 1) * 4)
        S.draw_text(d, (S.W // 2, bar_y + 150), str(sec), int(110 * pop), (255, 255, 255))
        yield im
    cell = S.GRID_SIZE / r["n"]
    rad = cell * 0.62
    centers = [(S.GRID_X + (a % r["n"] + 0.5) * cell, S.GRID_Y + (a // r["n"] + 0.5) * cell) for a in r["answers"]]
    reveal = base.copy()
    shade = Image.new("RGBA", (S.W, S.H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shade)
    sd.rectangle((S.GRID_X, S.GRID_Y, S.GRID_X + S.GRID_SIZE, S.GRID_Y + S.GRID_SIZE), fill=(0, 0, 0, 140))
    for cx, cy in centers:
        sd.ellipse((cx - rad, cy - rad, cx + rad, cy + rad), fill=(0, 0, 0, 0))
    reveal.alpha_composite(shade)
    labels = " · ".join(S.cell_label(a, r["n"]) for a in sorted(r["answers"], key=lambda a: (a % r["n"], a // r["n"])))
    for f in range(int(REVEAL * S.FPS)):
        im = reveal.copy()
        d = ImageDraw.Draw(im)
        grow = min(1, f / 6)
        rr = rad * (1.6 - 0.6 * grow)
        for cx, cy in centers:
            d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=(255, 40, 40), width=14)
        S.draw_text(d, (S.W // 2, bar_y + 110), "정답!", 100, (255, 230, 60))
        S.draw_text(d, (S.W // 2, bar_y + 220), labels, 72, (255, 255, 255))
        yield im


def outro_frames(bg, theme):
    base = bg.copy()
    d = ImageDraw.Draw(base)
    S.draw_text(d, (S.W // 2, 760), "몇 개 찾았어요?", 120, (255, 255, 255))
    S.draw_text(d, (S.W // 2, 950), "댓글로 알려주세요", 70, theme[2], stroke=6)
    S.draw_text(d, (S.W // 2, 1060), "예: B2 E5 G7", 56, (255, 255, 255), stroke=5)
    S.draw_text(d, (S.W // 2, 1300), f"{S.CHANNEL} {S.HANDLE}", 46, (255, 255, 255), stroke=0)
    for _ in range(int(S.OUTRO * S.FPS)):
        yield base


def make_audio(total, path, date):
    import music
    a = music.bed(total, date, "evening")

    def add(sig, at):
        i = int(at * S.SR)
        a[i:i + len(sig)] += sig[: len(a) - i]

    for s in range(int(SHOW)):
        add(S.tone(1500 if s >= int(SHOW) - 3 else 1000, 0.08, 40, 0.35), s)
    add(S.tone(880, 0.8, 5, 0.35) + S.tone(1320, 0.8, 6, 0.2), SHOW)
    t0 = SHOW + REVEAL
    for s in range(int(S.BONUS_SHOW)):
        add(S.tone(1500 if s == int(S.BONUS_SHOW) - 1 else 1000, 0.08, 40, 0.35), t0 + s)
    add(S.tone(880, 0.8, 5, 0.35) + S.tone(1320, 0.8, 6, 0.2), t0 + S.BONUS_SHOW)
    add(S.tone(660, 0.5, 4, 0.3) + S.tone(990, 0.5, 4, 0.2), t0 + S.BONUS_SHOW + S.BONUS_REVEAL)
    a = np.clip(a, -1, 1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(S.SR)
        w.writeframes((a * 32767).astype(np.int16).tobytes())


def make_metadata(rng, date, r, quiz):
    kind = r["kind"]
    if kind == "color":
        name = next(c for limit, c in S.COLOR_NAMES if r["hue"] < limit) + " " + S.SHAPE_KO[r.get("shape", "square")]
    elif kind == "icon":
        name = S.ICON_NAMES.get(r["pair"].split("|")[0], "그림")
    else:
        name = S.NAMES.get(r["pair"][0], "그림")
    e = (r["pair"] or "")[:1] if kind in ("emoji", "mirror") else ""
    hook = HOOKS.get(kind, HOOKS["emoji"]).format(name=name, n=r["n"] ** 2, e=e).strip()
    seen = S.recent_titles(date)
    tails = [t for t in TAILS if f"【다른 그림 찾기】 {hook} | {t} #shorts" not in seen] or TAILS
    title = f"【다른 그림 찾기】 {hook} | {rng.choice(tails)} #shorts"[:100]
    loc = {}
    for lang, (pre, h, tl, desc, tags) in LOC.items():
        hl = h.format(n=r["n"] ** 2, e=e or ("🎨" if kind == "color" else "👀")).strip()
        cands = [c for c in (f"{pre} {hl} | {t} #shorts" for t in rng.sample(tl, len(tl))) if S.utf16_len(c) <= 97]
        loc[lang] = {"title": cands[0] if cands else f"{pre} {hl} #shorts", "description": "\n".join(desc + ["", " ".join(tags)])}
    n = r["n"]
    return {
        "date": date, "format": "find3", "title": title,
        "description": "\n".join([
            "12초 안에 다른 그림 3개를 모두 찾아보세요! 🔍",
            "찾은 칸 3개를 댓글로 남겨주세요 (예: B2 E5 G7) 👇",
            f"{S.CHANNEL}에서 매일 새로운 눈썰미 테스트가 올라옵니다. 구독하고 매일 도전하세요!",
            "", "Find all 3 odd ones in 12 seconds!", "", " ".join(S.HASHTAGS)]),
        "defaultLanguage": "ko", "localizations": loc,
        "tags": [h.lstrip("#") for h in S.HASHTAGS] + ["눈썰미", "숨은그림찾기", "odd one out", "find 3 differences"],
        "categoryId": "24", "madeForKids": False, "containsSyntheticMedia": False, "style": r["style"],
        "bonus": quiz,
        "rounds": [{"kind": kind, "pair": r["pair"], "grid": n,
                    "answer_row": r["answers"][0] // n + 1, "answer_col": r["answers"][0] % n + 1,
                    "answers": [[a // n + 1, a % n + 1] for a in r["answers"]],
                    **({"shape": r["shape"]} if "shape" in r else {})}],
    }


def build(args, rng, rounds, uploaded, history):
    r = dict(rounds[-1])
    r["n"] = max(r["n"], 7)
    past = [(m["rounds"][-1]["answer_row"] - 1, m["rounds"][-1]["answer_col"] - 1, m["rounds"][-1]["grid"])
            for m in S.recent_meta(args.date, days=4)]
    r["answers"] = pick_three(rng, r["n"], past)
    r["answer"] = r["answers"][0]
    theme = S.THEMES[S.datetime.strptime(args.date, "%Y-%m-%d").toordinal() % len(S.THEMES)]
    bg = S.background(theme)
    out = S.OUT_DIR / args.date
    out.mkdir(parents=True, exist_ok=True)
    quiz = S.pick_quiz(args.date)
    total = SHOW + REVEAL + S.BONUS_SHOW + S.BONUS_REVEAL + S.OUTRO
    wav = out / "audio.wav"
    make_audio(total, wav, args.date)
    mp4 = out / "short.mp4"
    proc = subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{S.W}x{S.H}", "-r", str(S.FPS), "-i", "-",
        "-i", str(wav), "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", str(mp4),
    ], stdin=subprocess.PIPE)
    grid, _ = S.render_grid(r, rng)
    for k, frame in enumerate(puzzle_frames(r, grid, bg, theme)):
        rgb = frame.convert("RGB")
        if k == 0:
            rgb.save(out / "cover.jpg", quality=90)
        proc.stdin.write(rgb.tobytes())
    for frame in S.make_bonus_frames(quiz, bg, theme):
        proc.stdin.write(frame.convert("RGB").tobytes())
    for frame in outro_frames(bg, theme):
        proc.stdin.write(frame.convert("RGB").tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise SystemExit("ffmpeg 인코딩 실패")
    wav.unlink()
    meta = make_metadata(rng, args.date, r, quiz) | uploaded
    (out / "metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    history[args.date] = [r["pair"]] if r["pair"] else []
    S.HISTORY.write_text(json.dumps(dict(sorted(history.items())), ensure_ascii=False, indent=1))
    print(f"완료: {mp4} ({total:.1f}초, 3개 찾기)  제목: {meta['title']}")
