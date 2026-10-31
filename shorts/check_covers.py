"""최근 API로 올린 영상의 표지(맞춤 미리보기 이미지)가 실제로 들어갔는지 확인하고, 빠졌으면 다시 지정한다.

10/29: L2YljQHJNig는 업로드 때 '표지 지정: 완료'였는데 채널 쇼츠 목록에 2단계 장면이 표지로 나왔다.
맞춤 표지가 들어간 영상은 썸네일 주소에 sqp= 값이 붙는다(유튜브가 고른 장면이면 없다).
10/31: 쇼츠 3편 모두 비공개 예약 중에는 표지가 들어가 있다가 공개되자 빠졌다. 유튜브가 공개된 쇼츠에는
맞춤 표지 대신 영상 장면을 쓰는 것으로 보고, 공개된 쇼츠는 다시 지정하지 않는다(긴 영상은 계속 확인).

사용법:
    python3 shorts/check_covers.py            # 최근 7일
    python3 shorts/check_covers.py --days 14
"""
import argparse
import json
from datetime import datetime, timedelta

import requests

from upload import KST, ROOT, access_token

KINDS = (("output", "cover.jpg", "저녁"), ("output_one", "cover.jpg", "낮"), ("output_long", "thumbnail.jpg", "긴 영상"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    args = ap.parse_args()
    since = (datetime.now(KST) - timedelta(days=args.days)).strftime("%Y-%m-%d")

    todo = {}
    for folder, cover, label in KINDS:
        for meta_path in sorted((ROOT / folder).glob("*/metadata.json")):
            if meta_path.parent.name < since:
                continue
            meta = json.loads(meta_path.read_text())
            if meta.get("videoId") and meta.get("uploadedBy") == "api" and (meta_path.parent / cover).exists():
                todo[meta["videoId"]] = (meta_path.parent / cover, f"{label} {meta_path.parent.name}", folder == "output_long")
    if not todo:
        print("확인할 영상 없음")
        return

    headers = {"Authorization": f"Bearer {access_token()}"}
    r = requests.get("https://www.googleapis.com/youtube/v3/videos",
                     params={"part": "snippet,status", "id": ",".join(todo)}, headers=headers, timeout=30)
    r.raise_for_status()
    items = {v["id"]: v for v in r.json().get("items", [])}
    for vid, (cover, label, long) in todo.items():
        if vid not in items:
            print(f"{label} {vid}: 영상을 찾지 못함")
        elif "sqp=" in items[vid]["snippet"]["thumbnails"]["default"]["url"]:
            print(f"{label} {vid}: 표지 정상")
        elif not long and items[vid]["status"]["privacyStatus"] == "public":
            print(f"{label} {vid}: 공개된 쇼츠라 유튜브가 영상 장면을 표지로 씀(다시 지정 안 함)")
        else:
            t = requests.post("https://www.googleapis.com/upload/youtube/v3/thumbnails/set",
                              params={"videoId": vid}, headers={**headers, "Content-Type": "image/jpeg"},
                              data=cover.read_bytes(), timeout=120)
            print(f"{label} {vid}: 표지 빠짐 → 다시 지정 " + ("완료(반영까지 몇 분 걸릴 수 있음)" if t.ok else
                  f"실패 ({t.status_code}: {t.json().get('error', {}).get('message', '')})"))


if __name__ == "__main__":
    main()
