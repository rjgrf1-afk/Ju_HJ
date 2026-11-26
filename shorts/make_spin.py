"""낮 12시 자리 '회전 방향 착시' 쇼츠 (5주차 결정, 매주 수·토).

검은 그림자 사람이 제자리에서 도는데, 앞뒤 깊이가 없어 보는 사람마다 시계 방향/반시계 방향으로 다르게 보인다.
남의 그림·영상은 쓰지 않는다: 공 여러 개로 사람 모양을 직접 만들고(포즈는 날짜마다 다름) 평행 투영 그림자만 그린다.
우리 영상만의 부분: 중간에 '앞쪽을 밝게 칠한' 도움 화면을 두 번(시계 방향 → 반시계 방향) 보여 줘서
방향을 바꾸는 요령을 알려 준 뒤, 다시 그림자로 돌아가 혼자 바꿔 보게 한다.

  0~6초   그림자만 (어느 쪽으로 보이나요?)
  6~9초   도움 1: 앞쪽을 밝게 → 시계 방향으로 보임
  9~12초  도움 2: 반대로 칠함 → 반시계 방향으로 보임
  12~16초 그림자만 (이제 생각만으로 바꿔 보세요, 댓글로)

결과: shorts/output_one/<날짜>/ 에 short.mp4, cover.jpg, metadata.json (format "spin")
make_one.py가 수·토요일에 이 스크립트를 부른다. 단독 실행: python3 shorts/make_spin.py --date 2026-11-18
"""
import argparse
import json
import math
import random
import subprocess
import wave
from datetime import datetime, timedelta, timezone

import numpy as np
from PIL import Image, ImageDraw

import make_short as S

OUT_DIR = S.ROOT / "output_one"
W, H, FPS = S.W, S.H, S.FPS
TOTAL = 16.0
PHASES = [(0, 6, None), (6, 9, "cw"), (9, 12, "ccw"), (12, 16, None)]
SPIN_DAYS = (2, 5)  # 수, 토

HOOKS = ["이 그림자, 어느 쪽으로 돌아요? 🌀", "시계 방향? 반시계 방향? 보는 사람마다 달라요 🌀",
         "같은 그림자인데 방향이 바뀌어 보여요 🌀", "당신 눈에는 어느 쪽으로 돌아요? 🌀"]
TAILS = ["뇌가 정하는 방향", "처음엔 어느 쪽이었나요?", "몇 초 만에 바뀌었나요?", "도움 화면 보고 바꿔 보세요"]
LOC = {
    "en": ("【Optical Illusion】", ["Which way is she spinning? 🌀", "Clockwise or counterclockwise? 🌀"],
           ["Your brain decides", "Can you switch it?"],
           ["Clockwise or counterclockwise? The shadow has no depth, so your brain picks a direction.",
            "Watch the hint at 6s, then try to flip it with your mind. Comment which way you saw first 👇"],
           ["#shorts", "#opticalillusion", "#illusion", "#braintest", "#brainteaser"]),
    "ja": ("【錯視】", ["どっちに回ってる？🌀", "時計回り？反時計回り？🌀"], ["脳が決める向き", "切り替えられる？"],
           ["影には奥行きがないので、回る向きは脳が決めます。", "6秒のヒントを見てから、頭の中で向きを変えてみて。最初どっちに見えたかコメントしてね 👇"],
           ["#shorts", "#錯視", "#脳トレ", "#認知症予防", "#目の錯覚"]),
    "es": ("【Ilusión】", ["¿Hacia dónde gira? 🌀", "¿Horario o antihorario? 🌀"], ["Tu cerebro decide", "¿Puedes cambiarlo?"],
           ["La sombra no tiene profundidad: tu cerebro elige el sentido.", "Mira la pista a los 6 s y cámbialo con la mente. Comenta cómo lo viste primero 👇"],
           ["#shorts", "#ilusionoptica", "#retovisual", "#juegomental"]),
    "pt-BR": ("【Ilusão】", ["Para que lado ela gira? 🌀", "Horário ou anti-horário? 🌀"], ["Seu cérebro decide", "Consegue trocar?"],
              ["A sombra não tem profundidade: o cérebro escolhe o sentido.", "Veja a dica aos 6 s e troque com a mente. Comente como viu primeiro 👇"],
              ["#shorts", "#ilusaodeotica", "#testedevisao", "#desafio"]),
    "hi": ("【Optical Illusion】", ["Which way is she spinning? 🌀", "Clockwise or anticlockwise? 🌀"], ["Your brain decides", "Can you switch it?"],
           ["छाया में गहराई नहीं होती, इसलिए दिशा दिमाग तय करता है।", "6 सेकंड का हिंट देखो और मन से दिशा बदलो। पहले कौन सी दिशा दिखी, कमेंट करो 👇"],
           ["#shorts", "#opticalillusion", "#braintest"]),
    "id": ("【Ilusi Optik】", ["Dia berputar ke arah mana? 🌀", "Searah jarum jam atau berlawanan? 🌀"], ["Otakmu yang memilih", "Bisa kamu balik?"],
           ["Bayangan tidak punya kedalaman, jadi otak yang memilih arahnya.", "Lihat petunjuk di detik 6, lalu balik arahnya dengan pikiran. Tulis arah pertama yang kamu lihat 👇"],
           ["#shorts", "#ilusioptik", "#tesotak", "#asahotak"]),
}
TAGS = ["착시", "착시현상", "두뇌게임", "치매예방", "눈썰미", "optical illusion", "spinning illusion", "brain test"]


def cap(a, b, r1, r2):
    a, b = np.array(a, float), np.array(b, float)
    n = max(2, int(np.linalg.norm(b - a) / (min(r1, r2) * 0.5)))
    return [(a + (b - a) * t, r1 + (r2 - r1) * t) for t in np.linspace(0, 1, n)]


def figure(rng):
    """한 발로 선 사람. 팔·든 다리·머리 묶음 방향을 날짜마다 다르게 (어느 방향에서 봐도 좌우가 비대칭이어야 착시가 산다)."""
    P = []
    P += cap((0, 100, 0), (0, 140, 0), 13, 11)
    P += [(np.array((0, 160, 2.0)), 10)]
    P += cap((-2, 100, 0), (-2, 55, 0), 7, 5) + cap((-2, 55, 0), (-1, 8, 0), 5, 3.5) + cap((-2, 8, 0), (6, 6, 0), 3, 2.5)
    lift = rng.uniform(-0.9, 0.9)          # 든 다리가 뒤·옆으로 향하는 각
    lh = rng.uniform(50, 85)               # 무릎 높이
    k = (26 * math.cos(lift), lh + 4, -26 * math.sin(lift) - 18)
    f = (48 * math.cos(lift), lh - 16, -48 * math.sin(lift) - 40)
    P += cap((4, 102, 0), k, 7, 5) + cap(k, f, 5, 3.5)
    for side in (1, -1):                   # 팔: 높이·앞뒤가 서로 다르게
        up = rng.uniform(-10, 34)
        fw = rng.uniform(-24, 24)
        e = (side * 24, 140 + up * 0.5, fw * 0.5)
        h = (side * 44, 140 + up, fw)
        P += cap((0, 136, 0), e, 4.5, 3.5) + cap(e, h, 3.5, 3)
    tail = rng.uniform(-1, 1)
    P += cap((-4 * tail, 148, -2), (6 * tail, 170, -9), 5, 2)
    if rng.random() < 0.6:                 # 치마 띠 (반은 넣고 반은 뺀다)
        P += cap((-10, 95, -3), (14, 96, 5), 4, 4) + cap((-13, 90, -7), (17, 88, 9), 3, 3)
    return P


def arrow(rng):
    """납작한 화살표(앞뒤 두께 없음)를 작은 공으로 채운다. 세로축으로 돌면 어느 쪽으로 도는지 정해지지 않는다.
    미국 240만·멕시코 454만·일본 127만 회 소재 (research/2026-11-16.md, 2026-11-24.md)."""
    P = []
    y0 = rng.uniform(95, 115)
    length, head = rng.uniform(80, 100), rng.uniform(30, 40)
    shaft_h, head_h = rng.uniform(14, 20), rng.uniform(44, 56)
    x0 = -length / 2
    step = 3.0
    x = x0
    while x <= x0 + length:
        if x < x0 + length - head:
            half = shaft_h / 2
        else:
            half = head_h / 2 * (x0 + length - x) / head
        y = -half
        while y <= half:
            P.append((np.array((x, y0 + y, 0.0)), 2.6))
            y += step
        x += step
    # 기둥(받침) — 바닥에서 화살표 가운데까지
    P += cap((0, 8, 0), (0, y0 - shaft_h / 2, 0), 2.5, 2.5)
    return P


def shape_for(date):
    """착시 편 소재를 돌려 쓴다: 사람 → 화살표 → 사람 … (11/26부터, 같은 그림자 반복 방지)"""
    n = len(recent_spins(date, days=60))
    return "arrow" if n % 2 == 1 else "person"


def render(P, th, hint, scale, cx, cy, theme):
    SS = 2
    im = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pts = []
    for c, r in P:
        x = c[0] * math.cos(th) + c[2] * math.sin(th)
        z = -c[0] * math.sin(th) + c[2] * math.cos(th)  # 보는 사람 쪽이 +
        pts.append((x, c[1], z, r))
    if hint:
        # 실제 깊이(z)대로 칠하면 위에서 볼 때 반시계 방향, 깊이를 뒤집어 칠하면 시계 방향으로 보인다.
        # 가까운 쪽(나중에 그리는 쪽)을 밝게 칠한다.
        sgn = 1 if hint == "ccw" else -1
        pts.sort(key=lambda p: sgn * p[2])
        near = [sgn * p[2] for p in pts]
        lo, span = min(near), (max(near) - min(near)) or 1
    for x, y, z, r in pts:
        if hint:
            g = int(25 + 150 * (sgn * z - lo) / span)
            col = (g, g, g, 255)
        else:
            col = (18, 18, 22, 255)
        X, Y, R = (cx + x * scale) * SS, (cy - y * scale) * SS, r * scale * SS
        d.ellipse((X - R, Y - R, X + R, Y + R), fill=col)
    return im.resize((W, H), Image.LANCZOS)


def floor_arrow(d, cx, cy, hint, t, color):
    """바닥 타원 위 화살표: 앞쪽 가장자리가 움직이는 방향 (cw: 앞쪽이 왼쪽으로, ccw: 앞쪽이 오른쪽으로)."""
    rx, ry = 230, 46
    d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), outline=color, width=6)
    k = 1 if hint == "cw" else -1
    a = math.pi / 2 + k * (0.15 + 0.9 * ((t * 0.8) % 1))  # 앞쪽(아래)에서 시작해 옆으로 흐름
    ax, ay = cx + rx * math.cos(a), cy + ry * math.sin(a)
    tx, ty = -rx * math.sin(a) * k, ry * math.cos(a) * k
    n = math.hypot(tx, ty) or 1
    tx, ty = tx / n, ty / n
    s = 34
    d.polygon([(ax + tx * s, ay + ty * s), (ax - ty * s * 0.6, ay + tx * s * 0.6), (ax + ty * s * 0.6, ay - tx * s * 0.6)], fill=color)


def make_audio(path, date):
    import music
    a = music.bed(TOTAL, date, "spin", slow=1.5)  # 착시 편은 느리게

    def add(sig, at):
        i = int(at * S.SR)
        a[i:i + len(sig)] += sig[: len(a) - i]

    for at in (6, 9, 12):
        add(S.tone(880, 0.6, 5, 0.3) + S.tone(1320, 0.6, 6, 0.15), at)
    a = np.clip(a, -1, 1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(S.SR)
        w.writeframes((a * 32767).astype(np.int16).tobytes())


def recent_spins(date, days=28):
    day = datetime.strptime(date, "%Y-%m-%d")
    out = []
    for k in range(1, days + 1):
        f = OUT_DIR / (day - timedelta(days=k)).strftime("%Y-%m-%d") / "metadata.json"
        if f.exists():
            m = json.loads(f.read_text())
            if m.get("format") == "spin":
                out.append(m)
    return out


ARROW_HOOKS = ["이 화살표, 어느 쪽으로 돌아요? 🌀", "화살표가 도는 방향, 생각만으로 바꿀 수 있나요? 🌀",
               "3%만 거꾸로 돌릴 수 있는 화살표 🌀"]
ARROW_LOC = {"en": ["Which way is the arrow spinning? 🌀", "Only 3% can reverse this arrow 🌀"],
             "hi": ["Which way is the arrow spinning? 🌀", "Only 3% can reverse this arrow 🌀"],
             "es": ["¿Hacia dónde gira la flecha? 🌀"], "pt-BR": ["Para que lado a seta gira? 🌀"],
             "ja": ["3%しか逆に回せない矢印🌀", "この矢印、どっちに回ってる？🌀"], "id": ["Panah ini berputar ke arah mana? 🌀"]}
JA_EXTRA = ["10人中9人が逆に回せない錯視🌀", "頭の中で逆回転できる？🌀"]  # 일본 상위 착시 제목 형식 (11/16·11/24 연구)


def make_metadata(rng, date, pose, shape="person"):
    seen = {m["title"] for m in recent_spins(date)}
    hooks = ARROW_HOOKS if shape == "arrow" else HOOKS
    combos = [(h, t) for h in hooks for t in TAILS if f"【착시】 {h} | {t} #shorts" not in seen]
    hook, tail = rng.choice(combos or [(h, t) for h in hooks for t in TAILS])
    title = f"【착시】 {hook} | {tail} #shorts"
    loc = {}
    for lang, (pre, hooks, tails, desc, tags) in LOC.items():
        hs = ARROW_LOC[lang] if shape == "arrow" else hooks + (JA_EXTRA if lang == "ja" else [])
        cands = [f"{pre} {h} | {t} #shorts" for h in hs for t in tails]
        seen_l = {m.get("localizations", {}).get(lang, {}).get("title") for m in recent_spins(date)}
        cands = [c for c in cands if S.utf16_len(c) <= 97]
        loc[lang] = {"title": next((c for c in rng.sample(cands, len(cands)) if c not in seen_l), cands[0]),
                     "description": "\n".join(desc + ["", " ".join(tags)])}
    desc = "\n".join([
        ("화살표" if shape == "arrow" else "검은 그림자") + "가 시계 방향으로 도나요, 반시계 방향으로 도나요? 🌀",
        "그림자에는 앞뒤 깊이가 없어서, 어느 쪽으로 도는지는 눈이 아니라 뇌가 정합니다.",
        "6초부터 앞쪽을 밝게 칠한 도움 화면이 나와요. 본 뒤에 생각만으로 방향을 바꿔 보세요.",
        "처음에 어느 쪽으로 보였는지 댓글로 남겨 주세요 (시계 / 반시계) 👇",
        "",
        f"{S.CHANNEL}에서 매일 눈썰미 테스트와 착시 문제가 올라옵니다.",
        "",
        "#shorts #착시 #착시현상 #두뇌게임 #치매예방 #눈썰미테스트",
    ])
    return {
        "date": date, "format": "spin", "title": title[:100], "description": desc,
        "defaultLanguage": "ko", "localizations": loc, "tags": TAGS, "categoryId": "24",
        "madeForKids": False, "containsSyntheticMedia": False, "pose": pose, "shape": shape,
        "rounds": [{"kind": "spin"}],
    }


def main(date=None, force=False):
    if date is None:
        ap = argparse.ArgumentParser()
        ap.add_argument("--date", default=datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d"))
        ap.add_argument("--force", action="store_true")
        a = ap.parse_args()
        date, force = a.date, a.force
    out = OUT_DIR / date
    old = out / "metadata.json"
    uploaded = {k: v for k, v in json.loads(old.read_text()).items()
                if k in ("videoId", "publishAt", "uploadedBy")} if old.exists() else {}
    if uploaded.get("videoId") and not force:
        raise SystemExit(f"{date} 낮 영상은 이미 올렸습니다 ({uploaded['videoId']}). 다시 만들려면 --force")

    rng = random.Random(f"nunsseulmi-spin-{date}")
    shape = shape_for(date)
    P = arrow(rng) if shape == "arrow" else figure(rng)
    period = rng.uniform(2.2, 2.8)          # 한 바퀴 도는 시간
    theme = S.THEMES[(datetime.strptime(date, "%Y-%m-%d").toordinal() + 2) % len(S.THEMES)]
    bg = S.background(theme)
    base = bg.copy()
    d0 = ImageDraw.Draw(base)
    S.draw_text(d0, (W // 2, 125), S.CHANNEL, 40, (255, 255, 255, 200), stroke=0)
    # 그림자가 잘 보이게 밝은 판 위에 그린다
    d0.rounded_rectangle((90, 520, W - 90, 1560), radius=40, fill=(245, 245, 248, 255))
    cx, cy, scale = W // 2, 1450, 4.9

    out.mkdir(parents=True, exist_ok=True)
    wav = out / "audio.wav"
    make_audio(wav, date)
    mp4 = out / "short.mp4"
    proc = subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", str(wav),
        "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", str(mp4),
    ], stdin=subprocess.PIPE)
    for f in range(int(TOTAL * FPS)):
        t = f / FPS
        hint = next(h for a, b, h in PHASES if a <= t < b)
        im = base.copy()
        d = ImageDraw.Draw(im)
        if t < 6:
            S.draw_text(d, (W // 2, 240), "어느 쪽으로 돌아요?", 92, (255, 255, 255))
            S.draw_text(d, (W // 2, 370), "시계 방향? 반시계 방향?", 62, theme[2], stroke=6)
            S.draw_text(d, (W // 2, 455), "Which way is it spinning?" if shape == "arrow" else "Which way is she spinning?", 40, (255, 255, 255), stroke=4)
        elif hint:
            S.draw_text(d, (W // 2, 240), "도움 화면", 80, (255, 255, 255))
            S.draw_text(d, (W // 2, 370), "시계 방향으로 보면" if hint == "cw" else "반시계 방향으로 보면", 66, theme[2], stroke=6)
            S.draw_text(d, (W // 2, 455), "앞쪽을 밝게 칠했어요", 44, (255, 255, 255), stroke=4)
        else:
            S.draw_text(d, (W // 2, 240), "이제 생각만으로", 88, (255, 255, 255))
            S.draw_text(d, (W // 2, 370), "방향을 바꿔 보세요!", 70, theme[2], stroke=6)
            S.draw_text(d, (W // 2, 455), "Now flip it with your mind", 40, (255, 255, 255), stroke=4)
        th = 2 * math.pi * t / period
        im.alpha_composite(render(P, th, hint, scale, cx, cy, theme))
        if hint:
            floor_arrow(d, cx, cy + 14, hint, t, (230, 60, 60))
        else:
            d.ellipse((cx - 150, cy + 4, cx + 150, cy + 26), fill=(205, 205, 210, 255))
        if t >= 12:
            S.draw_text(d, (W // 2, 1690), "처음엔 어느 쪽이었나요? 댓글로!", 56, (255, 230, 60), stroke=6)
        rgb = im.convert("RGB")
        if f == 0:
            rgb.save(out / "cover.jpg", quality=90)
        proc.stdin.write(rgb.tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise SystemExit("ffmpeg 인코딩 실패")
    wav.unlink()
    meta = make_metadata(rng, date, {"period": round(period, 2)}, shape) | uploaded
    old.write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    print(f"완료: {mp4} ({TOTAL:.0f}초)  제목: {meta['title']}")


if __name__ == "__main__":
    main()
