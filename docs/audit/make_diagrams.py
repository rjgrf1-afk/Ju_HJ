"""YouTube API 감사 신청용 다이어그램(아키텍처, 사용자 흐름)을 그린다.

    python3 docs/audit/make_diagrams.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent
W, H = 1600, 900
INK, MUTED, LINE = (29, 26, 51), (97, 92, 122), (120, 110, 170)
BOX, GOOGLE, NOTE = (238, 235, 250), (230, 244, 234), (255, 247, 214)
F = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


KO = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"


def font(size, bold=False, ko=False):
    return ImageFont.truetype(KO if ko else FB if bold else F, size)


def box(d, x, y, w, h, title, lines, fill=BOX, ts=22, ls=17):
    d.rounded_rectangle((x, y, x + w, y + h), radius=14, fill=fill, outline=LINE, width=2)
    d.text((x + 16, y + 14), title, font=font(ts, True), fill=INK)
    for i, t in enumerate(lines):
        d.text((x + 16, y + 50 + i * 26), t, font=font(ls), fill=MUTED)
    return (x, y, w, h)


def arrow(d, a, b, label=""):
    d.line((a, b), fill=LINE, width=3)
    import math
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    for s in (-0.45, 0.45):
        d.line((b, (b[0] - 16 * math.cos(ang + s), b[1] - 16 * math.sin(ang + s))), fill=LINE, width=3)
    if label:
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        tw = d.textlength(label, font=font(15))
        d.rectangle((mx - tw / 2 - 6, my - 12, mx + tw / 2 + 6, my + 12), fill=(255, 255, 255))
        d.text((mx, my), label, font=font(15), fill=INK, anchor="mm")


def header(d, title, sub):
    d.text((50, 36), title, font=font(34, True), fill=INK)
    d.text((50, 84), sub, font=font(18), fill=MUTED)
    d.text((W - 50, 44), "OAuth app name: 눈썰미 연구소 업로더", font=font(20, ko=True), fill=MUTED, anchor="ra")


def architecture():
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    header(d, "Architecture - Nunsseulmi Lab Uploader",
           "Private script used only by the owner of YouTube channel @nunsseulmi_lab (UC7DlQBmVmLFcLiquvUfvKLw)")

    box(d, 50, 150, 330, 170, "Channel owner", ["Single user (no other users)", "Reviews each video",
                                                "Uploads manually until audit"])
    box(d, 470, 150, 420, 300, "Owner's private workspace", [
        "make_short.py", "  generates a 21s puzzle Short", "  (Python + ffmpeg, no user data)",
        "upload.py", "  uploads + schedules 18:00 KST", "Secrets: OAuth client ID/secret",
        "  and refresh token in environment", "  variables only (never in code)"])
    box(d, 470, 520, 420, 150, "GitHub repository", ["Source code, generated videos,",
                                                      "titles/descriptions. No tokens,",
                                                      "no personal or viewer data."])
    box(d, 1000, 150, 550, 130, "Google OAuth 2.0", ["oauth2.googleapis.com/token",
                                                     "refresh token -> short-lived access token"], GOOGLE)
    box(d, 1000, 330, 550, 160, "YouTube Data API v3", ["videos.insert (own channel, ~1/day)",
                                                        "channels.list mine=true",
                                                        "Scopes: youtube.upload, youtube.readonly"], GOOGLE)
    box(d, 1000, 540, 550, 130, "YouTube Analytics API", ["reports.query for own channel only",
                                                          "Scope: yt-analytics.readonly"], GOOGLE)

    arrow(d, (380, 235), (470, 235), "runs / reviews")
    arrow(d, (680, 450), (680, 520), "commit")
    arrow(d, (890, 215), (1000, 215), "token")
    arrow(d, (890, 380), (1000, 400), "upload")
    arrow(d, (890, 420), (1000, 590), "read stats")

    d.rounded_rectangle((50, 730, 1550, 860), radius=14, fill=NOTE)
    for i, t in enumerate([
        "Data handling: only the owner's own channel is accessed. No data is sold, shared, or used for ads.",
        "Nothing about viewers or other channels is collected. Access can be revoked at myaccount.google.com/permissions.",
        "Privacy policy: https://rjgrf1-afk.github.io/Ju_HJ/privacy.html",
    ]):
        d.text((74, 752 + i * 34), t, font=font(19), fill=INK)
    im.save(OUT / "architecture-diagram.png")


def user_flow():
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    header(d, "User flow - Nunsseulmi Lab Uploader", "The only user is the channel owner. Steps 2-6 repeat daily.")
    steps = [
        ("1. Authorize once", ["Owner signs in with", "Google, grants 3 scopes", "for own channel only"]),
        ("2. Generate", ["08:52 KST daily:", "make_short.py builds", "today's puzzle Short"]),
        ("3. Review", ["Answer position, text,", "audio are checked", "before upload"]),
        ("4. Upload", ["upload.py: videos.insert", "privacyStatus=private", "publishAt=18:00 KST"]),
        ("5. Publish", ["18:00 KST: YouTube", "publishes the Short", "on @nunsseulmi_lab"]),
        ("6. Learn", ["Next morning: read own", "views / retention via", "YouTube Analytics"]),
    ]
    bw, bh, gap, y = 230, 170, 24, 200
    cx = lambda i: 50 + i * (bw + gap) + bw / 2
    for i, (t, ls) in enumerate(steps):
        x = 50 + i * (bw + gap)
        box(d, x, y, bw, bh, t, ls, GOOGLE if i in (3, 4, 5) else BOX, ts=21, ls=16)
        if i < len(steps) - 1:
            arrow(d, (x + bw, y + bh / 2), (x + bw + gap, y + bh / 2))
    # 6 -> 2 로 돌아가는 매일 반복
    d.line(((cx(5), y + bh), (cx(5), 480), (cx(1), 480)), fill=LINE, width=3)
    arrow(d, (cx(1), 480), (cx(1), y + bh))
    d.text(((cx(1) + cx(5)) / 2, 500), "repeats every day", font=font(16), fill=MUTED, anchor="mm")

    d.rounded_rectangle((50, 620, 1550, 840), radius=14, fill=NOTE)
    for i, t in enumerate([
        "OAuth consent: the owner sees the Google consent screen of this app and approves:",
        "  youtube.upload (upload own videos), youtube.readonly (list own channel), yt-analytics.readonly (own stats).",
        "The refresh token is stored as a private environment variable of the owner's workspace.",
        "Revoke: myaccount.google.com/permissions -> the script immediately loses access.",
        "Expected volume: about 1 upload and a few read calls per day (well under the default quota).",
    ]):
        d.text((74, 640 + i * 38), t, font=font(19), fill=INK)
    im.save(OUT / "user-flow-diagram.png")


if __name__ == "__main__":
    architecture()
    user_flow()
    print("done")
