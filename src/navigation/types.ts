import { UserProfile } from '../types';

export type RootStackParamList = {
  Input: undefined;
  Results: { profile: UserProfile };
  Detail: { benefitId: string; profile: UserProfile };
};
