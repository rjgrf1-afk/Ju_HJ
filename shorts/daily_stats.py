"""채널과 영상별 통계를 모아 shorts/stats/<날짜>.json에 저장한다 (읽기 전용).

직접 앱으로 올린 영상도 포함되도록 채널의 업로드 목록에서 영상을 찾는다.
분석 지표(시청 지속률 등)는 유튜브 쪽에서 1~2일 늦게 채워진다.

사용법:
    python3 shorts/daily_stats.py
"""
import json
from datetime import datetime, timedelta

from channel_report import get
from upload import KST, ROOT, access_token

DATA = "https://www.googleapis.com/youtube/v3/"
ANALYTICS = "https://youtubeanalytics.googleapis.com/v2/reports"
VIDEO_METRICS = ["views", "estimatedMinutesWatched", "averageViewDuration",
                 "averageViewPercentage", "likes", "comments", "shares",
                 "subscribersGained", "subscribersLost"]


def main():
    token = access_token()
    today = datetime.now(KST).date()

    ch = get(DATA + "channels", token, {"part": "snippet,statistics,contentDetails", "mine": "true"})["items"][0]
    uploads = ch["contentDetails"]["relatedPlaylists"]["uploads"]

    ids, page = [], None
    while True:
        r = get(DATA + "playlistItems", token, {"part": "contentDetails", "playlistId": uploads,
                                                "maxResults": 50, **({"pageToken": page} if page else {})})
        ids += [i["contentDetails"]["videoId"] for i in r.get("items", [])]
        page = r.get("nextPageToken")
        if not page:
            break

    videos = []
    for i in range(0, len(ids), 50):
        r = get(DATA + "videos", token, {"part": "snippet,status,statistics", "id": ",".join(ids[i:i + 50])})
        for v in r.get("items", []):
            st = v["statistics"]
            videos.append({
                "id": v["id"],
                "title": v["snippet"]["title"],
                "publishedAt": v["snippet"]["publishedAt"],
                "privacyStatus": v["status"]["privacyStatus"],
                "views": int(st.get("viewCount", 0)),
                "likes": int(st.get("likeCount", 0)),
                "comments": int(st.get("commentCount", 0)),
            })

    # 영상별 분석 지표 (채널 개설 이후 누적)
    rep = get(ANALYTICS, token, {
        "ids": "channel==MINE", "startDate": "2026-10-01", "endDate": today.isoformat(),
        "metrics": ",".join(VIDEO_METRICS), "dimensions": "video", "sort": "-views", "maxResults": 200,
    })
    analytics = {row[0]: dict(zip(VIDEO_METRICS, row[1:])) for row in rep.get("rows") or []}
    for v in videos:
        v["analytics"] = analytics.get(v["id"])

    # 최근 7일 채널 일별 지표. engagedViews(넘기지 않고 본 조회)가 수익 창출 기준에 들어가는 조회수다
    daily = get(ANALYTICS, token, {
        "ids": "channel==MINE", "startDate": (today - timedelta(days=6)).isoformat(),
        "endDate": today.isoformat(), "metrics": "views,engagedViews,subscribersGained,subscribersLost",
        "dimensions": "day", "sort": "day",
    })

    st = ch["statistics"]
    out = {
        "collectedAt": datetime.now(KST).isoformat(timespec="seconds"),
        "channel": {"subscribers": int(st.get("subscriberCount", 0)),
                    "videos": int(st.get("videoCount", 0)),
                    "views": int(st.get("viewCount", 0))},
        "daily": [dict(zip(["day", "views", "engagedViews", "subscribersGained", "subscribersLost"], r))
                  for r in daily.get("rows") or []],
        "videos": sorted(videos, key=lambda v: v["publishedAt"]),
    }
    path = ROOT / "stats" / f"{today}.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1))

    c = out["channel"]
    print(f"구독자 {c['subscribers']} · 영상 {c['videos']} · 총 조회수 {c['views']}")
    for v in out["videos"]:
        a = v["analytics"] or {}
        print(f"- {v['publishedAt'][:10]} {v['privacyStatus']:8} 조회 {v['views']:>6} 좋아요 {v['likes']:>4} "
              f"댓글 {v['comments']:>3} 평균시청률 {a.get('averageViewPercentage', '-')}%  {v['id']}")
    print(f"저장: {path.relative_to(ROOT.parent)}")


if __name__ == "__main__":
    main()
