"""배경 음악: 직접 합성(저작권 걱정 없음). 11/17 채널 주인 '음악좀 바꿔보자'.

10/19부터 모든 영상이 같은 6음 반복이었다(research/2026-11-17.md: 채널 단위 '같은 틀' 신호).
음계 × 악기 소리 × 리듬 무늬 × 빠르기를 조합한 8가지 곡을 만들고, 날짜와 형식(저녁/낮/긴 영상/착시)으로 고른다.
같은 날 저녁과 낮은 항상 다른 곡이 나오고, 같은 형식은 8일에 한 번만 같은 곡이 돈다.
"""
import hashlib
from datetime import datetime

import numpy as np

SR = 44100

# 반음 단위 음계
SCALES = {
    "장조 5음": [0, 2, 4, 7, 9],
    "단조 5음": [0, 3, 5, 7, 10],
    "리디안": [0, 2, 4, 6, 7, 9, 11],
    "도리안": [0, 2, 3, 5, 7, 9, 10],
}

# (이름, 음계, 으뜸음 Hz, 악기, 무늬, 한 박 초, 베이스)
PRESETS = [
    ("밝은 종소리", "장조 5음", 261.6, "bell", "up", 0.25, True),
    ("통통 튀는 플럭", "장조 5음", 293.7, "pluck", "updown", 0.22, False),
    ("차분한 오르골", "리디안", 349.2, "musicbox", "walk", 0.30, False),
    ("살짝 긴장되는 단조", "단조 5음", 220.0, "soft", "updown", 0.26, True),
    ("부드러운 사인", "장조 5음", 196.0, "sine", "broken", 0.28, True),
    ("재즈풍 도리안", "도리안", 246.9, "pluck", "walk", 0.24, True),
    ("맑은 마림바", "리디안", 329.6, "marimba", "up", 0.20, False),
    ("느긋한 단조 종", "단조 5음", 261.6, "bell", "broken", 0.32, False),
]
OFFSET = {"evening": 0, "one": 3, "long": 5, "spin": 6}


def _voice(kind, freq, dur, vol):
    t = np.arange(int(SR * dur)) / SR
    if kind == "bell":       # 종: 배음이 정수배가 아님, 길게 울림
        s = np.sin(2 * np.pi * freq * t) + 0.4 * np.sin(2 * np.pi * freq * 2.76 * t) * np.exp(-t * 6)
        env = np.exp(-t * 3.5)
    elif kind == "pluck":    # 뜯는 소리: 홀수 배음, 빨리 줄어듦
        s = np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(2 * np.pi * freq * 3 * t) + 0.12 * np.sin(2 * np.pi * freq * 5 * t)
        env = np.exp(-t * 9)
    elif kind == "musicbox":
        s = np.sin(2 * np.pi * freq * 2 * t) + 0.25 * np.sin(2 * np.pi * freq * 4 * t)
        env = np.exp(-t * 5)
    elif kind == "marimba":
        s = np.sin(2 * np.pi * freq * t) + 0.5 * np.sin(2 * np.pi * freq * 4 * t) * np.exp(-t * 25)
        env = np.exp(-t * 7)
    elif kind == "soft":     # 삼각파에 가까운 부드러운 소리
        s = np.sin(2 * np.pi * freq * t) - np.sin(2 * np.pi * freq * 3 * t) / 9 + np.sin(2 * np.pi * freq * 5 * t) / 25
        env = np.minimum(1, t / 0.03) * np.exp(-t * 4)
    else:                    # sine
        s = np.sin(2 * np.pi * freq * t)
        env = np.minimum(1, t / 0.02) * np.exp(-t * 5)
    return vol * s * env / max(1e-9, np.abs(s).max())


def preset_for(date, fmt):
    """날짜와 형식으로 곡을 고른다. 같은 날 저녁과 낮은 항상 다르다."""
    day = datetime.strptime(date, "%Y-%m-%d").toordinal()
    return PRESETS[(day + OFFSET.get(fmt, 0)) % len(PRESETS)]


def bed(total, date, fmt, vol=0.06, slow=1.0):
    """길이 total초 배경음(+1초 여유). slow는 박을 늘리는 배수(긴 영상 2.0)."""
    name, scale, root, inst, pattern, beat, bass = preset_for(date, fmt)
    beat *= slow
    rng = np.random.default_rng(int(hashlib.md5(f"{date}-{fmt}".encode()).hexdigest()[:8], 16))
    degrees = SCALES[scale]
    notes = [root * 2 ** ((d + 12 * o) / 12) for o in (0, 1) for d in degrees]
    n = len(notes)
    a = np.zeros(int(SR * total) + SR)

    def add(sig, at):
        i = int(at * SR)
        if i < len(a):
            a[i:i + len(sig)] += sig[: len(a) - i]

    idx = 0
    step = 1
    for k in range(int(total / beat)):
        if pattern == "up":
            idx = k % n
        elif pattern == "updown":
            idx += step
            if idx >= n - 1 or idx <= 0:
                step = -step
            idx = max(0, min(n - 1, idx))
        elif pattern == "broken":   # 1-3-2-4 식 꺾은 아르페지오
            idx = [0, 2, 1, 3, 2, 4, 3, 5][k % 8] % n
        else:                        # walk: 이웃 음으로 무작위 걸음
            idx = int(np.clip(idx + rng.choice([-2, -1, 1, 2]), 0, n - 1))
        add(_voice(inst, notes[idx], beat * 1.8, vol), k * beat)
        if bass and k % 4 == 0:
            add(_voice("sine", root / 2, beat * 3.5, vol * 0.9), k * beat)
    return a
