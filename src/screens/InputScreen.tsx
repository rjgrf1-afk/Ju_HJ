import { NativeStackScreenProps } from '@react-navigation/native-stack';
import React, { useEffect, useState } from 'react';
import {
  Alert,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Chip } from '../components/Chip';
import { NumberField } from '../components/NumberField';
import { RegionPickerModal } from '../components/RegionPickerModal';
import { CONDITION_OPTIONS } from '../data/labels';
import { regionName } from '../data/regions';
import { loadProfile, saveProfile } from '../lib/storage';
import { RootStackParamList } from '../navigation/types';
import { ConditionKey, RegionCode, UserProfile } from '../types';

type Props = NativeStackScreenProps<RootStackParamList, 'Input'>;

export default function InputScreen({ navigation }: Props) {
  const [region, setRegion] = useState<RegionCode | null>(null);
  const [regionModalVisible, setRegionModalVisible] = useState(false);
  const [age, setAge] = useState(0);
  const [householdSize, setHouseholdSize] = useState(1);
  const [monthlyIncome, setMonthlyIncome] = useState(0);
  const [conditions, setConditions] = useState<ConditionKey[]>([]);

  useEffect(() => {
    loadProfile().then((saved) => {
      if (!saved) return;
      setRegion(saved.region);
      setAge(saved.age);
      setHouseholdSize(saved.householdSize);
      setMonthlyIncome(saved.monthlyIncome);
      setConditions(saved.conditions);
    });
  }, []);

  function toggleCondition(key: ConditionKey) {
    setConditions((prev) => (prev.includes(key) ? prev.filter((c) => c !== key) : [...prev, key]));
  }

  async function handleSubmit() {
    if (!region) {
      Alert.alert('거주 지역을 선택해주세요');
      return;
    }
    if (age <= 0) {
      Alert.alert('나이를 입력해주세요');
      return;
    }
    if (householdSize <= 0) {
      Alert.alert('가구원 수를 입력해주세요');
      return;
    }

    const profile: UserProfile = {
      region,
      age,
      householdSize,
      monthlyIncome,
      conditions,
    };

    await saveProfile(profile);
    navigation.navigate('Results', { profile });
  }

  return (
    <SafeAreaView style={styles.safeArea} edges={['top', 'bottom']}>
      <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
        <Text style={styles.heading}>내 정보로{'\n'}받을 수 있는 혜택 찾기</Text>
        <Text style={styles.subheading}>
          입력한 정보는 기기에만 저장되며, 혜택 매칭에만 사용됩니다.
        </Text>

        <View style={styles.field}>
          <Text style={styles.label}>거주 지역</Text>
          <Pressable style={styles.selectBox} onPress={() => setRegionModalVisible(true)}>
            <Text style={region ? styles.selectValue : styles.selectPlaceholder}>
              {region ? regionName(region) : '지역을 선택하세요'}
            </Text>
            <Text style={styles.chevron}>›</Text>
          </Pressable>
        </View>

        <NumberField label="나이" value={age} onChange={setAge} suffix="세" placeholder="예: 32" />

        <NumberField
          label="가구원 수"
          value={householdSize}
          onChange={setHouseholdSize}
          suffix="명"
          placeholder="본인 포함"
          helperText="본인을 포함한 함께 사는 가족 수를 입력하세요"
        />

        <NumberField
          label="가구 월 소득"
          value={monthlyIncome}
          onChange={setMonthlyIncome}
          suffix="만원"
          placeholder="세전 합산 소득"
          helperText="가구원 전체의 세전 월 소득 합계 (근사치도 괜찮아요)"
        />

        <View style={styles.field}>
          <Text style={styles.label}>해당하는 항목을 모두 선택하세요</Text>
          <View style={styles.chipWrap}>
            {CONDITION_OPTIONS.map((opt) => (
              <Chip
                key={opt.key}
                label={opt.label}
                selected={conditions.includes(opt.key)}
                onPress={() => toggleCondition(opt.key)}
              />
            ))}
          </View>
        </View>

        <Pressable style={styles.submitButton} onPress={handleSubmit}>
          <Text style={styles.submitButtonText}>받을 수 있는 혜택 확인하기</Text>
        </Pressable>

        <Text style={styles.disclaimer}>
          ※ 결과는 참고용이며, 실제 지원 여부와 금액은 복지로·정부24 또는 관할 기관에서 반드시 확인하세요.
        </Text>
      </ScrollView>

      <RegionPickerModal
        visible={regionModalVisible}
        selected={region}
        onSelect={setRegion}
        onClose={() => setRegionModalVisible(false)}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#F5F7FB',
  },
  container: {
    padding: 20,
    paddingBottom: 40,
  },
  heading: {
    fontSize: 26,
    fontWeight: '800',
    color: '#1D2433',
    lineHeight: 34,
    marginTop: 8,
    marginBottom: 8,
  },
  subheading: {
    fontSize: 14,
    color: '#6B7383',
    marginBottom: 28,
  },
  field: {
    marginBottom: 20,
  },
  label: {
    fontSize: 15,
    fontWeight: '600',
    color: '#1D2433',
    marginBottom: 8,
  },
  selectBox: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#D8DEE9',
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 14,
    backgroundColor: '#FFFFFF',
  },
  selectValue: {
    fontSize: 16,
    color: '#1D2433',
  },
  selectPlaceholder: {
    fontSize: 16,
    color: '#9AA3B2',
  },
  chevron: {
    fontSize: 20,
    color: '#9AA3B2',
  },
  chipWrap: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  submitButton: {
    backgroundColor: '#2F6FED',
    borderRadius: 14,
    paddingVertical: 16,
    alignItems: 'center',
    marginTop: 12,
  },
  submitButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },
  disclaimer: {
    marginTop: 16,
    fontSize: 12,
    color: '#9AA3B2',
    lineHeight: 18,
  },
});
