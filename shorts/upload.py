"""만든 쇼츠를 YouTube에 예약 업로드한다 (YouTube Data API v3).

필요한 환경 변수 (README의 '계정 연결' 참고):
    YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN

사용법:
    python3 shorts/upload.py --date 2026-10-20            # 그날 18:00 KST 공개 예약
    python3 shorts/upload.py --date 2026-10-20 --now      # 바로 공개
    python3 shorts/upload.py --date 2026-10-20 --private  # 비공개 (예약 공개 없음)
    python3 shorts/upload.py --long --date 2026-11-06     # 긴 영상 (output_long/<날짜>), 그날 18:00 공개 예약
    python3 shorts/upload.py --one --date 2026-10-30      # 낮 한 문제 쇼츠 (output_one/<날짜>), 그날 12:00 공개 예약
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
ONE_HOUR = 12  # 낮 한 문제 쇼츠 (점심시간)


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
    kind = ap.add_mutually_exclusive_group()
    kind.add_argument("--long", action="store_true", help="주간 긴 영상 (output_long/<날짜>/long.mp4)")
    kind.add_argument("--one", action="store_true", help="낮 12시 한 문제 쇼츠 (output_one/<날짜>/short.mp4)")
    vis = ap.add_mutually_exclusive_group()
    vis.add_argument("--now", action="store_true", help="예약 없이 바로 공개")
    vis.add_argument("--private", action="store_true", help="비공개로만 올림 (예약 공개 없음)")
    args = ap.parse_args()

    out = ROOT / ("output_long" if args.long else "output_one" if args.one else "output") / args.date
    video_file, cover = ("long.mp4", "thumbnail.jpg") if args.long else ("short.mp4", "cover.jpg")
    link = "https://youtu.be/" if args.long else "https://youtube.com/shorts/"
    meta = json.loads((out / "metadata.json").read_text())
    if meta.get("videoId"):
        raise SystemExit(f"이미 업로드됨: {link}{meta['videoId']}")

    status = {
        "selfDeclaredMadeForKids": meta["madeForKids"],
        "containsSyntheticMedia": meta["containsSyntheticMedia"],
    }
    if args.now:
        status["privacyStatus"] = "public"
    elif args.private:
        status["privacyStatus"] = "private"
    else:
        publish = datetime.strptime(args.date, "%Y-%m-%d").replace(hour=ONE_HOUR if args.one else PUBLISH_HOUR,
                                                                   tzinfo=KST)
        status["privacyStatus"] = "private"  # publishAt은 private일 때만 동작
        status["publishAt"] = publish.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    body = {
        "snippet": {
            "title": meta["title"],
            "description": meta["description"],
            "tags": meta["tags"],
            "categoryId": meta["categoryId"],
            "defaultLanguage": "ko",
            "defaultAudioLanguage": "ko",
        },
        "status": status,
    }
    # 언어별 제목·설명 (youtube.upload 권한으로 함께 넣을 수 있다)
    parts = "snippet,status"
    if meta.get("localizations"):
        body["localizations"] = meta["localizations"]
        parts += ",localizations"
    video = (out / video_file).read_bytes()
    headers = {"Authorization": f"Bearer {access_token()}"}

    init = requests.post(
        "https://www.googleapis.com/upload/youtube/v3/videos",
        params={"uploadType": "resumable", "part": parts},
        headers={**headers, "X-Upload-Content-Type": "video/mp4",
                 "X-Upload-Content-Length": str(len(video))},
        json=body, timeout=60)
    init.raise_for_status()
    up = requests.put(init.headers["Location"], data=video,
                      headers={**headers, "Content-Type": "video/mp4"}, timeout=600)
    up.raise_for_status()

    meta["videoId"] = up.json()["id"]
    meta["publishAt"] = status.get("publishAt", "private" if args.private else "now")
    meta["uploadedBy"] = "api"
    (out / "metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    print(f"업로드 완료: {link}{meta['videoId']} (공개: {meta['publishAt']})")

    # 표지: 쇼츠는 유튜브가 아무 장면(정답 장면일 수도 있음)을 고르므로 첫 화면을 직접 지정해 본다.
    # 채널에 맞춤 미리보기 이미지 권한이 없거나 쇼츠에서 막히면 실패해도 업로드는 그대로 둔다
    if (out / cover).exists():
        t = requests.post("https://www.googleapis.com/upload/youtube/v3/thumbnails/set",
                          params={"videoId": meta["videoId"]},
                          headers={**headers, "Content-Type": "image/jpeg"},
                          data=(out / cover).read_bytes(), timeout=120)
        print("표지 지정: " + ("완료" if t.ok else f"실패 ({t.status_code}: {t.json().get('error', {}).get('message', '')})"))

    # 올라간 상태 확인 (예약 시간이 그대로인지, 처리 중 거부되지 않았는지)
    r = requests.get("https://www.googleapis.com/youtube/v3/videos",
                     params={"part": "status", "id": meta["videoId"]}, headers=headers, timeout=30)
    st = (r.json().get("items") or [{}])[0].get("status", {})
    print(f"상태: {st.get('privacyStatus')} · 예약 {st.get('publishAt')} · 처리 {st.get('uploadStatus')}"
          + (f" · 거부 사유 {st.get('rejectionReason')}" if st.get("rejectionReason") else ""))


if __name__ == "__main__":
    main()
