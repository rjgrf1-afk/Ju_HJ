import { BenefitCategory, ConditionKey } from '../types';

export const CATEGORY_LABELS: Record<BenefitCategory, string> = {
  livelihood: '생계·의료·교육',
  childcare: '임신·출산·양육',
  youth: '청년',
  housing: '주거',
  senior: '어르신',
  disability: '장애인',
  family: '한부모·다자녀·신혼',
  job: '취업·근로',
  energy: '에너지·생활비',
  local: '지역 한정',
};

export const CONDITION_OPTIONS: { key: ConditionKey; label: string }[] = [
  { key: 'pregnant', label: '임신 중이거나 출산 예정이에요' },
  { key: 'infant', label: '만 6세 이하 자녀가 있어요' },
  { key: 'minorChild', label: '미성년 자녀가 있어요' },
  { key: 'multiChild', label: '자녀가 2명 이상이에요' },
  { key: 'singleParent', label: '한부모·조손 가정이에요' },
  { key: 'disability', label: '가구원 중 등록 장애인이 있어요' },
  { key: 'elderlyMember', label: '만 65세 이상 가구원이 있어요' },
  { key: 'newlywed', label: '신혼부부(혼인 7년 이내)예요' },
  { key: 'jobSeeking', label: '구직 활동 중이에요' },
  { key: 'employed', label: '현재 일하고 있어요(근로·사업소득)' },
  { key: 'farmerFisher', label: '농업·어업에 종사해요' },
  { key: 'singlePerson', label: '1인 가구예요' },
  { key: 'currentRecipient', label: '이미 기초생활수급자예요' },
];
