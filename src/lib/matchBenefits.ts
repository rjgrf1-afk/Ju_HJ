import { BENEFITS } from '../data/benefits';
import { calcIncomePercent } from '../data/regions';
import { Benefit, UserProfile } from '../types';

const CATEGORY_ORDER: Benefit['category'][] = [
  'livelihood',
  'childcare',
  'family',
  'housing',
  'job',
  'youth',
  'senior',
  'disability',
  'energy',
  'local',
];

export function matchBenefits(profile: UserProfile): Benefit[] {
  const incomePercent = calcIncomePercent(profile.monthlyIncome, profile.householdSize);

  return BENEFITS.filter((benefit) => {
    if (benefit.regions && !benefit.regions.includes(profile.region)) {
      return false;
    }
    return benefit.isEligible(profile, incomePercent);
  }).sort((a, b) => CATEGORY_ORDER.indexOf(a.category) - CATEGORY_ORDER.indexOf(b.category));
}

export function incomePercentForProfile(profile: UserProfile): number {
  return calcIncomePercent(profile.monthlyIncome, profile.householdSize);
}
