import { RegionCode } from '../types';

export const REGIONS: { code: RegionCode; name: string }[] = [
  { code: 'seoul', name: '서울특별시' },
  { code: 'busan', name: '부산광역시' },
  { code: 'daegu', name: '대구광역시' },
  { code: 'incheon', name: '인천광역시' },
  { code: 'gwangju', name: '광주광역시' },
  { code: 'daejeon', name: '대전광역시' },
  { code: 'ulsan', name: '울산광역시' },
  { code: 'sejong', name: '세종특별자치시' },
  { code: 'gyeonggi', name: '경기도' },
  { code: 'gangwon', name: '강원특별자치도' },
  { code: 'chungbuk', name: '충청북도' },
  { code: 'chungnam', name: '충청남도' },
  { code: 'jeonbuk', name: '전북특별자치도' },
  { code: 'jeonnam', name: '전라남도' },
  { code: 'gyeongbuk', name: '경상북도' },
  { code: 'gyeongnam', name: '경상남도' },
  { code: 'jeju', name: '제주특별자치도' },
];

export function regionName(code: RegionCode): string {
  return REGIONS.find((r) => r.code === code)?.name ?? code;
}

// 2025년 기준 중위소득 (원/월, 가구원수별) — 참고용 수치이며 매년 변경됩니다.
// 실제 지원 여부는 반드시 복지로/정부24에서 최신 공고를 확인하세요.
export const MEDIAN_INCOME_BY_HOUSEHOLD: Record<number, number> = {
  1: 2392013,
  2: 3932658,
  3: 5025353,
  4: 6097773,
  5: 7108192,
  6: 8064805,
  7: 8988428,
};

export function medianIncomeForHousehold(size: number): number {
  const capped = Math.min(Math.max(size, 1), 7);
  if (MEDIAN_INCOME_BY_HOUSEHOLD[capped]) return MEDIAN_INCOME_BY_HOUSEHOLD[capped];
  // 8인 이상은 1인 증가시마다 7인 기준 증가분만큼 가산 (근사치)
  const extra = size - 7;
  const step = MEDIAN_INCOME_BY_HOUSEHOLD[7] - MEDIAN_INCOME_BY_HOUSEHOLD[6];
  return MEDIAN_INCOME_BY_HOUSEHOLD[7] + step * extra;
}

// 월 소득(만원)과 가구원수를 받아 기준 중위소득 대비 % 를 계산 (근사치, 참고용)
export function calcIncomePercent(monthlyIncomeManwon: number, householdSize: number): number {
  const medianWon = medianIncomeForHousehold(householdSize);
  const incomeWon = monthlyIncomeManwon * 10000;
  return Math.round((incomeWon / medianWon) * 100);
}
