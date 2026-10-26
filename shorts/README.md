# 눈썰미 연구소 쇼츠

말 없이 보는 "다른 하나 찾기" 퀴즈 쇼츠를 매일 한 편 자동으로 만든다.

```bash
python3 shorts/make_short.py                 # 오늘(KST) 영상
python3 shorts/make_short.py --date 2026-10-20
python3 shorts/upload.py --date 2026-10-20   # 18:00 KST 공개 예약 (계정 연결 필요)
```

결과물은 `shorts/output/<날짜>/`에 생긴다.

- `short.mp4`: 1080×1920, 21초
- `metadata.json`: 제목, 설명, 태그, 정답 위치
- `preview.png`: 3단계 첫 화면

통계는 `python3 shorts/daily_stats.py`로 모은다. 채널과 영상별 조회수, 좋아요, 댓글, 시청 지속률, 구독자 증감을 `shorts/stats/<날짜>.json`에 쌓는다(앱으로 직접 올린 영상도 포함).

쓴 이모지 쌍은 `history.json`에 기록해 다음 날 겹치지 않게 한다.

## 업로드 (수동)
API 심사 전까지는 `short.mp4`를 받아 유튜브 앱에서 올리고, 제목과 설명은 `metadata.json`에서 복사한다.

## 계정 연결 (자동 업로드)
환경 변수 `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`을 설정한다(`youtube.upload` 권한).
심사받지 않은 API 프로젝트로 올린 영상은 비공개로 잠기므로 YouTube API 감사를 신청해야 공개 업로드가 된다.

## 라이선스
- 이모지: Noto Color Emoji (SIL OFL 1.1)
- 3D 그림: Microsoft Fluent Emoji 3D (MIT, `assets/fluent/LICENSE`). 홀수 날(날짜 서수 기준)에 쓴다
- 아이콘: Google Material Symbols Rounded (Apache 2.0, `assets/material/LICENSE`). 3단계 '아이콘 찾기'에 쓴다
- 효과음과 배경음은 코드로 합성한다
