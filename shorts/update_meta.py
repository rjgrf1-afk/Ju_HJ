"""이미 올린 영상의 제목·설명·태그·번역을 metadata.json 내용으로 고친다 (youtube.force-ssl 권한 필요).

예약 시각·공개 상태는 건드리지 않는다(part=snippet,localizations만 보낸다).

사용법:
    python3 shorts/update_meta.py --date 2026-10-29          # 저녁 3단계 쇼츠 (output/)
    python3 shorts/update_meta.py --one --date 2026-10-30    # 낮 한 문제 쇼츠 (output_one/)
    python3 shorts/update_meta.py --long --date 2026-10-31   # 긴 영상 (output_long/)
    --refresh: 영상을 다시 만들지 않고 해시태그·태그·영어 제목 앞부분만 지금 규칙으로 바꾼 뒤 올린다
               (make_short --force로 다시 만들면 그 사이 쌓인 기록 때문에 다른 문제가 뽑힐 수 있다)
"""
import argparse
import json

import requests

import make_short as S
from upload import ROOT, access_token


def refresh(meta, one):
    """제목(한국어)과 문제는 그대로 두고, 해시태그 줄·태그·번역의 해시태그와 영어 제목 앞부분만 지금 규칙으로 바꾼다."""
    kind = meta["rounds"][-1]["kind"]
    lines = meta["description"].split("\n")
    meta["description"] = "\n".join(lines[:-1] + [" ".join(S.HASHTAGS)])
    meta["tags"] = [h.lstrip("#") for h in S.HASHTAGS] + ["눈썰미", "숨은그림찾기", "odd one out"] \
        + (["find the odd one out"] if one else [])
    for lang, loc in (meta.get("localizations") or {}).items():
        L = S.LOCALES[lang]
        d = loc["description"].split("\n")
        loc["description"] = "\n".join(d[:-1] + [" ".join(S.loc_tags(L, kind))])
        if loc["title"].startswith(L["prefix"]):
            loc["title"] = S.loc_prefix(L, kind) + loc["title"][len(L["prefix"]):]
    return meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    kind = ap.add_mutually_exclusive_group()
    kind.add_argument("--long", action="store_true")
    kind.add_argument("--one", action="store_true")
    ap.add_argument("--refresh", action="store_true", help="해시태그·영어 제목 앞부분을 지금 규칙으로 바꾼 뒤 올린다")
    args = ap.parse_args()

    out = ROOT / ("output_long" if args.long else "output_one" if args.one else "output") / args.date
    meta = json.loads((out / "metadata.json").read_text())
    if not meta.get("videoId"):
        raise SystemExit(f"{out}에는 올린 기록(videoId)이 없습니다")
    if args.refresh:
        if args.long:
            raise SystemExit("긴 영상은 --refresh를 지원하지 않습니다")
        meta = refresh(meta, args.one)
        (out / "metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))

    body = {
        "id": meta["videoId"],
        "snippet": {
            "title": meta["title"],
            "description": meta["description"],
            "tags": meta["tags"],
            "categoryId": meta["categoryId"],
            "defaultLanguage": "ko",
            "defaultAudioLanguage": "ko",
        },
    }
    parts = "snippet"
    if meta.get("localizations"):
        body["localizations"] = meta["localizations"]
        parts += ",localizations"
    r = requests.put("https://www.googleapis.com/youtube/v3/videos", params={"part": parts},
                     headers={"Authorization": f"Bearer {access_token()}"}, json=body, timeout=60)
    if not r.ok:
        raise SystemExit(f"수정 실패 ({r.status_code}): {r.json().get('error', {}).get('message', '')}")
    v = r.json()
    print(f"수정 완료: {meta['videoId']} · 제목 '{v['snippet']['title'][:40]}…' · 번역 {sorted((v.get('localizations') or {}))}")


if __name__ == "__main__":
    main()
