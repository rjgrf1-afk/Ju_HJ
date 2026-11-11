"""낮 12시에 올리는 '11초 한 문제' 쇼츠를 만든다.

저녁 6시 3단계 쇼츠(make_short.py)와 같은 그림·검수 규칙을 쓴다. 극악 한 문제를 8초 동안 보여 주고 3초 동안 정답을 보여 준다.
빨리 크는 해외 퍼즐 채널이 모두 11초 한 문제 형식이라 시험한다(research/2026-10-28.md, experiments.md 실험 5).
같은 날 저녁 쇼츠가 먼저 만들어져 있으면 그 3단계와 유형·그림·정답 자리가 겹치지 않게 고른다.

결과: shorts/output_one/<날짜>/ 에 short.mp4, cover.jpg, metadata.json

사용법:
    python3 shorts/make_one.py --date 2026-10-30
"""
import argparse
import json
import random
import subprocess
import wave
from datetime import datetime, timedelta, timezone

import numpy as np
from PIL import ImageDraw

import make_short as S
from emoji_pool import HARD, ICON_NAMES, ICON_PAIRS, MIRROR, NAMES, NUMBER_PAIRS

OUT_DIR = S.ROOT / "output_one"
SHOW, REVEAL = 8.0, 3.0
# 숫자는 말이 필요 없어 해외에서도 통하므로 다른 유형보다 두 배 자주 낸다 (이틀 연속은 안 됨)
# 11/9 주간 결정: 숫자 문제가 넘기지 않고 본 비율 1위(11/6 연구) → 가중치 2 → 4. 이틀 연속 같은 유형은 막혀 있어 하루걸러 숫자가 된다
KINDS = {"number": 4, "hard": 1, "mirror": 1, "icon": 1, "color": 1}
LABEL = "FIND THE ODD ONE"

SUBJECTS = {
    "number": "{a} 사이에 다른 숫자 하나 🔢",
    "emoji": "{name} {n}개 중 딱 하나가 달라요 {e}",
    "mirror": "{name} {n}개 중 하나만 뒤집혀 있어요 {e}",
    "icon": "{name} 아이콘 {n}개 중 딱 하나가 달라요 👀",
    "color": "{name} {n}개 중 하나만 색이 달라요 🎨",
}
TAILS = ["8초 안에 찾으면 상위 1%", "한 번에 찾으면 눈썰미 천재", "점심시간 눈썰미 테스트", "못 찾으면 다시 보기 🔁"]
# 언어별 꼬리말과 설명 (제목 앞부분은 make_short.LOCALES를 같이 쓴다)
ONE_TEXT = {
    "ko": {"desc": ["8초 안에 다른 하나를 찾아보세요! 🔍", "한 번에 찾았는지 댓글로 남겨주세요 👇",
                    f"{S.CHANNEL}에서 매일 낮 12시 한 문제, 저녁 6시 3단계 문제가 올라옵니다. 구독하고 매일 도전하세요!"]},
    "en": {"tails": ["Find it in 8 seconds", "Can you spot it on the first try?", "Only sharp eyes see it", "Lunch break eye test"],
           "desc": ["Find the odd one out in 8 seconds! 🔍", "Did you get it on the first try? Comment below 👇",
                    "New puzzles every day. Subscribe and play daily!"]},
    "ja": {"tails": ["8秒で見つけられる？", "一発で見つけたら天才", "観察力に自信ある？", "お昼の脳トレ"],
           "desc": ["8秒で仲間はずれを見つけよう！🔍", "一発で見つけられたかコメントしてね 👇",
                    "毎日新しい問題を公開中。チャンネル登録して毎日挑戦しよう！"]},
    "es": {"tails": ["Encuéntralo en 8 segundos", "¿Lo ves a la primera?", "¿Tienes buen ojo?", "Reto rápido"],
           "desc": ["¡Encuentra el diferente en 8 segundos! 🔍", "¿Lo encontraste a la primera? Comenta 👇",
                    "Un nuevo reto visual cada día. ¡Suscríbete y juega a diario!"]},
    "pt-BR": {"tails": ["Ache em 8 segundos", "Você acha de primeira?", "Tem olho bom?", "Teste rápido"],
              "desc": ["Ache o diferente em 8 segundos! 🔍", "Achou de primeira? Comente 👇",
                       "Um novo teste de visão todo dia. Inscreva-se e jogue diariamente!"]},
    "hi": {"tails": ["8 सेकंड में ढूंढो", "क्या आप एक बार में ढूंढ पाएंगे?", "तेज़ नज़र वाले ही देखें", "आज का आई टेस्ट"],
           "desc": ["8 सेकंड में अलग वाला ढूंढो! 🔍", "क्या आपने पहली बार में ढूंढ लिया? कमेंट करें 👇",
                    "हर दिन एक नया आई टेस्ट। सब्सक्राइब करो और रोज़ खेलो!"]},
    "id": {"tails": ["Temukan dalam 8 detik", "Bisa langsung ketemu?", "Matamu tajam?", "Tes mata siang ini"],
           "desc": ["Cari yang beda dalam 8 detik! 🔍", "Langsung ketemu? Tulis di komentar 👇",
                    "Tes mata baru setiap hari. Subscribe dan main tiap hari!"]},
}


def recent_one(date, days=4):
    day = datetime.strptime(date, "%Y-%m-%d")
    out = []
    for k in range(1, days + 1):
        f = OUT_DIR / (day - timedelta(days=k)).strftime("%Y-%m-%d") / "metadata.json"
        if f.exists():
            out.append(json.loads(f.read_text()))
    return out


def build_one(rng, used, date, evening):
    """evening: 같은 날 저녁 쇼츠 metadata (없으면 None)."""
    recent = recent_one(date)
    # 11/5: 어제 저녁 3단계(색깔 49칸, 4줄 3칸)와 오늘 낮 문제가 유형·자리까지 똑같이 나온 일이 있어 어제 저녁도 피한다
    last_eve = (S.recent_meta(date, days=1) or [None])[0]
    norm = lambda k: "hard" if k == "emoji" else k
    avoid = {norm(m["rounds"][-1]["kind"]) for m in [recent[0] if recent else None, evening, last_eve] if m}
    kinds = [k for k in KINDS if k not in avoid]
    kind = rng.choices(kinds, weights=[KINDS[k] for k in kinds])[0]
    # 저녁 쇼츠와 그림체를 반대로 해서 같은 날 두 영상의 느낌이 다르게
    style = "noto" if S.style_for(date) == "fluent" else "fluent"
    styled = lambda pool: [p for p in pool if S.has_style(p, style)]
    metas = recent + S.recent_meta(date, days=4) + ([evening] if evening else [])
    seen = {c for m in metas for r in m["rounds"] if r["kind"] not in ("icon", "number")
            for c in S.emoji_chars(r["pair"])}
    # 11/8: 그림은 달라도 제목 이름이 같으면('웃는 얼굴' 😃 → 🙂) 제목이 거의 같아진다. 최근 제목에 나온 이름은 피한다
    recent_titles = " ".join(m["title"] for m in metas)
    fresh_name = lambda p: NAMES.get(p[0], "그림") == "그림" or NAMES.get(p[0]) not in recent_titles
    unseen = lambda pool: [p for p in pool if not seen & S.emoji_chars(p) and fresh_name(p)] or pool

    if kind == "hard":
        pair = S.pick(rng, unseen(styled(HARD)), used)
        r = {"kind": "emoji", "pair": pair[::-1] if len(pair) == 2 and rng.random() < 0.5 else pair, "n": 8}
    elif kind == "mirror":
        r = {"kind": "mirror", "pair": S.pick(rng, unseen(styled(MIRROR)), used), "n": 8}
    elif kind == "icon":
        icons = [p for p in ICON_PAIRS if ICON_NAMES.get(p[0], "그림") not in recent_titles] or ICON_PAIRS
        r = {"kind": "icon", "pair": S.pick(rng, ["|".join(p) for p in icons], used), "n": 8}
    elif kind == "number":
        # 11/10: 같은 숫자가 며칠 새 다시 나오지 않게(11/7 '77 사이 71' → 11/10 '17 사이 71') 최근 숫자 문제에 쓴 숫자는 피한다
        recent_nums = {x for m in recent_one(date, 10) for r in m["rounds"] if r["kind"] == "number" for x in r["pair"].split("|")}
        fresh = [p for p in NUMBER_PAIRS if "|".join(p) not in used and not recent_nums & set(p)]
        a, b = rng.choice(fresh or [p for p in NUMBER_PAIRS if "|".join(p) not in used] or NUMBER_PAIRS)
        r = {"kind": "number", "pair": f"{a}|{b}", "n": 8}
    else:
        shape, n = S.pick_color_look(rng, [m for m in [evening, last_eve] if m] + recent_one(date, 21) + S.recent_meta(date, 21))
        r = {"kind": "color", "pair": None, "n": n, "shape": shape}
    r["style"], r["label"] = style, LABEL
    # 같은 날 저녁 3단계 정답을 맨 앞(어제 자리)에 두어 화면에서 같은 줄·칸을 피한다
    past = [(m["rounds"][-1]["answer_row"] - 1, m["rounds"][-1]["answer_col"] - 1, m["rounds"][-1]["grid"])
            for m in ([evening] if evening else []) + ([last_eve] if last_eve else []) + recent]
    r["answer"] = S.pick_answer(rng, r["n"], past)
    return r


def header_one(base, theme, label):
    d = ImageDraw.Draw(base)
    S.draw_text(d, (S.W // 2, 125), S.CHANNEL, 40, (255, 255, 255, 200), stroke=0)
    S.draw_text(d, (S.W // 2, 230), "다른 하나를 찾아라!", 92, (255, 255, 255))
    S.draw_text(d, (S.W // 2, 360), "8초 안에 찾으면 상위 1%", 58, theme[2], stroke=6)
    d.rounded_rectangle((S.W // 2 - 270, 455, S.W // 2 + 270, 545), radius=45, fill=(0, 0, 0, 150))
    S.draw_text(d, (S.W // 2, 500), label, 50, (255, 255, 255), stroke=0)


def make_audio(path):
    total = SHOW + REVEAL
    a = np.zeros(int(S.SR * total) + S.SR)

    def add(sig, at):
        i = int(at * S.SR)
        a[i:i + len(sig)] += sig[: len(a) - i]

    notes = [261.6, 329.6, 392.0, 523.3, 392.0, 329.6]
    for k in range(int(total / 0.25)):
        add(S.tone(notes[k % len(notes)], 0.4, 6, 0.06), k * 0.25)
    for s in range(int(SHOW)):
        hi = s >= int(SHOW) - 3  # 마지막 3초는 높은 소리로 재촉
        add(S.tone(1500 if hi else 1000, 0.08, 40, 0.35), s)
    add(S.tone(880, 0.8, 5, 0.35) + S.tone(1320, 0.8, 6, 0.2), SHOW)
    a = np.clip(a, -1, 1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(S.SR)
        w.writeframes((a * 32767).astype(np.int16).tobytes())


def make_metadata(rng, date, r):
    kind = r["kind"]
    if kind == "color":
        name = next(c for limit, c in S.COLOR_NAMES if r["hue"] < limit) + " " + S.SHAPE_KO[r.get("shape", "square")]
    elif kind == "icon":
        name = ICON_NAMES.get(r["pair"].split("|")[0], "그림")
    elif kind == "number":
        name = ""
    else:
        name = NAMES.get(r["pair"][0], "그림")
    e = (r["pair"] or "")[:1] if kind in ("emoji", "mirror") else ""
    subject = SUBJECTS[kind].format(name=name, n=r["n"] ** 2, e=e,
                                    a=r["pair"].split("|")[0] if kind == "number" else "")
    seen = {m["title"] for m in recent_one(date, 14) + S.recent_meta(date, 14)}
    # 11/7: 저녁 쇼츠(11/5)처럼 같은 유형 최근 14일 영상의 꼬리말·번역 제목도 피한다
    # (숫자 문제 10/30·11/4의 영어 제목이 글자 하나까지 같았다)
    same_kind = [m for m in recent_one(date, 14) if m["rounds"][-1]["kind"] == kind]
    used_tails = {t for m in same_kind for t in TAILS if f"| {t}" in m["title"]}
    tails = [t for t in TAILS if f"【다른 하나 찾기】 {subject} | {t} #shorts" not in seen and t not in used_tails]
    title = f"【다른 하나 찾기】 {subject} | {rng.choice(tails or TAILS)} #shorts"
    tail_i = rng.randrange(2)
    localizations = {}
    for lang, L in S.LOCALES.items():
        T = ONE_TEXT[lang]
        hook = L["hooks"][kind].format(n=r["n"] ** 2, e=e)
        pre = S.loc_prefix(L, kind)
        options = [t for t in (f"{pre} {hook} | {t} #shorts" for t in [T["tails"][tail_i]] + T["tails"])
                   if S.utf16_len(t) <= 97]
        seen_l = {m.get("localizations", {}).get(lang, {}).get("title") for m in same_kind}
        localizations[lang] = {
            "title": next((t for t in options if t not in seen_l), options[0] if options else f"{pre} {hook} #shorts"),
            "description": "\n".join(T["desc"] + ["", " ".join(S.loc_tags(L, kind))]),
        }
    return {
        "date": date,
        "format": "one",
        "title": title[:100],
        "description": "\n".join(ONE_TEXT["ko"]["desc"] + ["", "Find the odd one out in 8 seconds!", "",
                                                          " ".join(S.HASHTAGS)]),
        "defaultLanguage": "ko",
        "localizations": localizations,
        "tags": [h.lstrip("#") for h in S.HASHTAGS] + ["눈썰미", "숨은그림찾기", "odd one out", "find the odd one out"],
        "categoryId": "24",
        "madeForKids": False,
        "containsSyntheticMedia": False,
        "style": r["style"],
        "rounds": [{"kind": kind, "pair": r["pair"], "grid": r["n"],
                    "answer_row": r["answer"] // r["n"] + 1, "answer_col": r["answer"] % r["n"] + 1,
                    **({"shape": r["shape"]} if "shape" in r else {})}],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d"))
    ap.add_argument("--force", action="store_true", help="이미 올린 날짜도 다시 만든다 (올린 영상은 그대로)")
    args = ap.parse_args()

    out = OUT_DIR / args.date
    old = out / "metadata.json"
    uploaded = {k: v for k, v in json.loads(old.read_text()).items()
                if k in ("videoId", "publishAt", "uploadedBy")} if old.exists() else {}
    if uploaded.get("videoId") and not args.force:
        raise SystemExit(f"{args.date} 낮 영상은 이미 올렸습니다 ({uploaded['videoId']}). 다시 만들려면 --force")

    key = f"{args.date}-one"
    rng = random.Random(f"nunsseulmi-one-{args.date}")
    history = json.loads(S.HISTORY.read_text()) if S.HISTORY.exists() else {}
    used = {p for d, ps in history.items() if d != key for p in ps}
    eve = S.OUT_DIR / args.date / "metadata.json"
    r = build_one(rng, used, args.date, json.loads(eve.read_text()) if eve.exists() else None)

    # 저녁 쇼츠와 다른 배경색
    theme = S.THEMES[(datetime.strptime(args.date, "%Y-%m-%d").toordinal() + 2) % len(S.THEMES)]
    bg = S.background(theme)
    out.mkdir(parents=True, exist_ok=True)
    wav = out / "audio.wav"
    make_audio(wav)
    mp4 = out / "short.mp4"
    proc = subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{S.W}x{S.H}", "-r", str(S.FPS), "-i", "-",
        "-i", str(wav),
        "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", str(mp4),
    ], stdin=subprocess.PIPE)
    grid, ans = S.render_grid(r, rng)
    for k, frame in enumerate(S.make_round_frames(r, grid, ans, bg, theme, SHOW, REVEAL, header_one)):
        rgb = frame.convert("RGB")
        if k == 0:  # 표지: 문제 첫 화면 (정답 장면이 표지가 되지 않게)
            rgb.save(out / "cover.jpg", quality=90)
        proc.stdin.write(rgb.tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise SystemExit("ffmpeg 인코딩 실패")
    wav.unlink()

    meta = make_metadata(rng, args.date, r) | uploaded
    old.write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    history[key] = [r["pair"]] if r["pair"] else []
    S.HISTORY.write_text(json.dumps(dict(sorted(history.items())), ensure_ascii=False, indent=1))
    print(f"완료: {mp4} ({SHOW + REVEAL:.0f}초)  제목: {meta['title']}")


if __name__ == "__main__":
    main()
