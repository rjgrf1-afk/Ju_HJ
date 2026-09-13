export type RegionCode =
  | 'seoul'
  | 'busan'
  | 'daegu'
  | 'incheon'
  | 'gwangju'
  | 'daejeon'
  | 'ulsan'
  | 'sejong'
  | 'gyeonggi'
  | 'gangwon'
  | 'chungbuk'
  | 'chungnam'
  | 'jeonbuk'
  | 'jeonnam'
  | 'gyeongbuk'
  | 'gyeongnam'
  | 'jeju';

export type ConditionKey =
  | 'pregnant'
  | 'infant' // 만 6세 이하 자녀
  | 'minorChild' // 미성년 자녀
  | 'multiChild' // 2자녀 이상
  | 'singleParent'
  | 'disability'
  | 'elderlyMember' // 만 65세 이상 가구원
  | 'newlywed'
  | 'jobSeeking'
  | 'employed'
  | 'farmerFisher'
  | 'singlePerson'
  | 'currentRecipient'; // 이미 기초생활수급자/차상위

export interface UserProfile {
  region: RegionCode;
  age: number;
  householdSize: number;
  monthlyIncome: number; // 세전 가구 합산 소득 (만원 단위)
  conditions: ConditionKey[];
}

export type BenefitCategory =
  | 'livelihood' // 생계·의료·주거·교육
  | 'childcare' // 임신·출산·양육
  | 'youth' // 청년
  | 'housing' // 주거
  | 'senior' // 어르신
  | 'disability' // 장애인
  | 'family' // 한부모·다자녀·신혼부부
  | 'job' // 취업·근로
  | 'energy' // 에너지·생활비 경감
  | 'local'; // 지역 한정

export interface Benefit {
  id: string;
  name: string;
  category: BenefitCategory;
  agency: string;
  summary: string;
  detail: string;
  applyMethod: string;
  link: string;
  regions?: RegionCode[]; // 지정 시 해당 지역만 해당, 없으면 전국 공통
  isEligible: (profile: UserProfile, incomePercent: number | null) => boolean;
}

export interface MatchedBenefit {
  benefit: Benefit;
}
