# 내 복지 찾기 (My Welfare Finder)

거주 지역, 나이, 가구원 수, 소득, 생활 조건 등 개인 정보를 입력하면 국가/지자체에서
받을 수 있는 복지 혜택을 찾아주는 모바일 앱입니다. Expo(React Native) + TypeScript로
제작되었으며 iOS, Android, 웹에서 동일하게 동작합니다.

## 주요 기능

- **정보 입력**: 거주 지역(17개 시·도), 나이, 가구원 수, 가구 월 소득, 생활 조건(임신·출산,
  자녀, 장애, 한부모, 청년, 구직 등)을 입력
- **자동 매칭**: 기준 중위소득 대비 소득 비율을 계산해 생계·의료·주거·교육급여, 근로·자녀장려금,
  청년 정책, 아동수당·부모급여, 기초연금, 장애인연금, 한부모 지원, 에너지바우처, 지역 한정
  혜택(서울시 청년수당, 경기도 청년기본소득 등) 등 20여 개 대표 제도와 자동으로 매칭
- **결과 목록/상세**: 매칭된 혜택을 카드 목록으로 보여주고, 상세 화면에서 설명·신청 방법·
  공식 사이트 링크 확인 가능
- **입력 정보 저장**: 마지막으로 입력한 정보를 기기에 저장해 다음 실행 시 자동으로 불러옴

> ⚠️ 이 앱의 혜택 정보는 참고용 요약이며, 선정 기준과 지원 금액은 매년 바뀝니다. 실제 신청
> 전에는 반드시 [복지로](https://www.bokjiro.go.kr) 또는 [정부24](https://www.gov.kr)에서
> 최신 공고를 확인하세요.

## 프로젝트 구조

```
App.tsx                     앱 진입점 (NavigationContainer 래핑)
src/
  types/                    UserProfile, Benefit 등 타입 정의
  data/
    regions.ts               17개 시·도 목록, 기준 중위소득(참고용) 계산
    benefits.ts               복지 제도 데이터셋 + 자격 조건 함수
    labels.ts                 카테고리/조건 항목 한글 라벨
  lib/
    matchBenefits.ts          사용자 정보 기반 혜택 매칭 엔진
    storage.ts                AsyncStorage 기반 입력 정보 저장/불러오기
  components/                 Chip, NumberField, RegionPickerModal 등 UI 컴포넌트
  screens/
    InputScreen.tsx            개인 정보 입력 화면
    ResultsScreen.tsx           매칭 결과 목록 화면
    DetailScreen.tsx            혜택 상세 화면
  navigation/
    RootNavigator.tsx           스택 내비게이션 설정
    types.ts                    내비게이션 파라미터 타입
```

## 실행 방법

```bash
npm install

# 개발 서버 실행 (아래 중 선택)
npm run web       # 브라우저에서 실행
npm run ios       # iOS 시뮬레이터 (macOS 필요)
npm run android   # Android 에뮬레이터
```

`npm start` 로 Expo 개발 서버를 띄운 뒤 Expo Go 앱으로 QR코드를 스캔해도 됩니다.

## 데이터 갱신

`src/data/benefits.ts`의 각 항목은 `isEligible(profile, incomePercent)` 함수로 자격 조건을
선언합니다. 새 제도를 추가하거나 기준을 갱신하려면 이 파일과 `src/data/regions.ts`의 기준
중위소득 표를 수정하면 됩니다.
