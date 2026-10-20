"""만든 쇼츠를 YouTube에 예약 업로드한다 (YouTube Data API v3).

필요한 환경 변수 (README의 '계정 연결' 참고):
    YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN

사용법:
    python3 shorts/upload.py --date 2026-10-20            # 그날 18:00 KST 공개 예약
    python3 shorts/upload.py --date 2026-10-20 --now      # 바로 공개
    python3 shorts/upload.py --date 2026-10-20 --private  # 비공개 (예약 공개 없음)
"""
import argparse
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
KST = timezone(timedelta(hours=9))
PUBLISH_HOUR = 18


def access_token():
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": os.environ["YT_CLIENT_ID"],
        "client_secret": os.environ["YT_CLIENT_SECRET"],
        "refresh_token": os.environ["YT_REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    }, timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=datetime.now(KST).strftime("%Y-%m-%d"))
    vis = ap.add_mutually_exclusive_group()
    vis.add_argument("--now", action="store_true", help="예약 없이 바로 공개")
    vis.add_argument("--private", action="store_true", help="비공개로만 올림 (예약 공개 없음)")
    args = ap.parse_args()

    out = ROOT / "output" / args.date
    meta = json.loads((out / "metadata.json").read_text())
    if meta.get("videoId"):
        raise SystemExit(f"이미 업로드됨: https://youtube.com/shorts/{meta['videoId']}")

    status = {
        "selfDeclaredMadeForKids": meta["madeForKids"],
        "containsSyntheticMedia": meta["containsSyntheticMedia"],
    }
    if args.now:
        status["privacyStatus"] = "public"
    elif args.private:
        status["privacyStatus"] = "private"
    else:
        publish = datetime.strptime(args.date, "%Y-%m-%d").replace(hour=PUBLISH_HOUR, tzinfo=KST)
        status["privacyStatus"] = "private"  # publishAt은 private일 때만 동작
        status["publishAt"] = publish.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    body = {
        "snippet": {
            "title": meta["title"],
            "description": meta["description"],
            "tags": meta["tags"],
            "categoryId": meta["categoryId"],
            "defaultLanguage": "ko",
        },
        "status": status,
    }
    video = (out / "short.mp4").read_bytes()
    headers = {"Authorization": f"Bearer {access_token()}"}

    init = requests.post(
        "https://www.googleapis.com/upload/youtube/v3/videos",
        params={"uploadType": "resumable", "part": "snippet,status"},
        headers={**headers, "X-Upload-Content-Type": "video/mp4",
                 "X-Upload-Content-Length": str(len(video))},
        json=body, timeout=60)
    init.raise_for_status()
    up = requests.put(init.headers["Location"], data=video,
                      headers={**headers, "Content-Type": "video/mp4"}, timeout=600)
    up.raise_for_status()

    meta["videoId"] = up.json()["id"]
    meta["publishAt"] = status.get("publishAt", "private" if args.private else "now")
    (out / "metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    print(f"업로드 완료: https://youtube.com/shorts/{meta['videoId']} (공개: {meta['publishAt']})")


if __name__ == "__main__":
    main()
