"""우리 채널 영상의 댓글에 채널 이름으로 답글 달기 (11/13 사용자 승인: '둘 다 하자').

  python3 shorts/reply_comments.py --list [--days 7]   # 아직 우리가 답하지 않은 댓글 보기
  python3 shorts/reply_comments.py --post replies.json  # {"댓글ID": "답글", ...} 올리기

규칙: 우리 채널 영상의 댓글에만 쓴다(다른 채널 금지). 답글은 Claude가 댓글마다 직접 쓴다(같은 문구 반복 금지).
링크·개인정보 금지. 욕설·광고·스팸 댓글에는 답하지 않는다. 올린 답글은 replies/<날짜>.json에 남긴다.
"""
import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
from upload import access_token  # noqa: E402

CHANNEL_ID = "UC7DlQBmVmLFcLiquvUfvKLw"
API = "https://www.googleapis.com/youtube/v3"
LOG_DIR = Path(__file__).parent / "replies"


def threads(headers, days):
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    out, token = [], None
    while True:
        p = {"part": "snippet,replies", "allThreadsRelatedToChannelId": CHANNEL_ID, "maxResults": 100, "order": "time"}
        if token:
            p["pageToken"] = token
        r = requests.get(f"{API}/commentThreads", params=p, headers=headers, timeout=30)
        r.raise_for_status()
        j = r.json()
        for it in j.get("items", []):
            top = it["snippet"]["topLevelComment"]["snippet"]
            if top["publishedAt"] < since:
                return out
            out.append(it)
        token = j.get("nextPageToken")
        if not token:
            return out


def answered(it):
    top = it["snippet"]["topLevelComment"]["snippet"]
    if top.get("authorChannelId", {}).get("value") == CHANNEL_ID:
        return True  # 우리가 쓴 댓글
    for rep in it.get("replies", {}).get("comments", []):
        if rep["snippet"].get("authorChannelId", {}).get("value") == CHANNEL_ID:
            return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--post")
    a = ap.parse_args()
    headers = {"Authorization": f"Bearer {access_token()}"}
    if a.list:
        todo = [it for it in threads(headers, a.days) if not answered(it)]
        ids = sorted({it["snippet"]["videoId"] for it in todo})
        titles = {}
        if ids:
            r = requests.get(f"{API}/videos", params={"part": "snippet", "id": ",".join(ids)}, headers=headers, timeout=30)
            titles = {v["id"]: v["snippet"]["title"] for v in r.json().get("items", [])}
        for it in todo:
            s = it["snippet"]["topLevelComment"]["snippet"]
            print(json.dumps({"id": it["id"], "at": s["publishedAt"][:16], "video": titles.get(it["snippet"]["videoId"], "")[:60],
                              "text": s["textOriginal"]}, ensure_ascii=False))
        print(f"답하지 않은 댓글 {len(todo)}개")
    if a.post:
        replies = json.loads(Path(a.post).read_text())
        LOG_DIR.mkdir(exist_ok=True)
        log_path = LOG_DIR / f"{datetime.now(timezone(timedelta(hours=9))):%Y-%m-%d}.json"
        log = json.loads(log_path.read_text()) if log_path.exists() else {}
        for cid, text in replies.items():
            r = requests.post(f"{API}/comments", params={"part": "snippet"}, headers=headers, timeout=30,
                              json={"snippet": {"parentId": cid, "textOriginal": text}})
            ok = r.ok
            print(f"{cid}: " + ("답글 완료" if ok else f"실패 ({r.status_code}: {r.json().get('error', {}).get('message', '')})"))
            if ok:
                log[cid] = text
        log_path.write_text(json.dumps(log, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
