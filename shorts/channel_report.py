"""내 채널의 기본 정보와 최근 28일 분석 지표를 읽어 표로 출력한다 (읽기 전용).

필요한 환경 변수 (README의 '계정 연결' 참고):
    YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN
    (youtube.readonly, yt-analytics.readonly 권한)

사용법:
    python3 shorts/channel_report.py
"""
import unicodedata
from datetime import datetime, timedelta

import requests

from upload import KST, access_token

METRICS = ["views", "estimatedMinutesWatched", "averageViewPercentage", "subscribersGained"]
DAYS = 28


def get(url, token, params):
    r = requests.get(url, params=params, headers={"Authorization": f"Bearer {token}"}, timeout=30)
    if not r.ok:
        err = r.json().get("error", {})
        raise SystemExit(f"API error {r.status_code}: {err.get('status')} {err.get('message')}")
    return r.json()


def width(s):
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in str(s))


def table(header, rows):
    widths = [max(map(width, col)) for col in zip(header, *rows)]
    line = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    fmt = lambda row: "| " + " | ".join(" " * (w - width(x)) + str(x) for x, w in zip(row, widths)) + " |"
    return "\n".join([line, fmt(header), line, *map(fmt, rows), line])


def main():
    token = access_token()

    ch = get("https://www.googleapis.com/youtube/v3/channels", token,
             {"part": "snippet,statistics", "mine": "true"})["items"][0]
    sn, st = ch["snippet"], ch["statistics"]
    print("== Channel (YouTube Data API v3 channels.list, mine=true) ==")
    print(table(["Title", "Handle", "Subscribers", "Videos", "Total views"], [[
        sn["title"], sn.get("customUrl", "-"),
        "hidden" if st.get("hiddenSubscriberCount") else st.get("subscriberCount", "0"),
        st.get("videoCount", "0"), st.get("viewCount", "0"),
    ]]))

    end = datetime.now(KST).date()
    start = end - timedelta(days=DAYS - 1)
    rep = get("https://youtubeanalytics.googleapis.com/v2/reports", token, {
        "ids": "channel==MINE",
        "startDate": start.isoformat(),
        "endDate": end.isoformat(),
        "metrics": ",".join(METRICS),
        "dimensions": "day",
        "sort": "day",
    })
    print()
    print(f"== Last {DAYS} days {start} ~ {end} (YouTube Analytics API reports.query) ==")
    rows = rep.get("rows") or []
    if not rows:
        print("아직 데이터 없음 (No analytics data yet)")
        return
    print(table(["day", *METRICS], rows))
    totals = [sum(r[1] for r in rows), sum(r[2] for r in rows),
              round(sum(r[3] for r in rows) / len(rows), 1), sum(r[4] for r in rows)]
    print(table(["total", *METRICS], [[f"{len(rows)} days", *totals]]))


if __name__ == "__main__":
    main()
