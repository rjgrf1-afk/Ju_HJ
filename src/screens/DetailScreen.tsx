import { NativeStackScreenProps } from '@react-navigation/native-stack';
import React from 'react';
import { Linking, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { CATEGORY_LABELS } from '../data/labels';
import { BENEFITS } from '../data/benefits';
import { regionName } from '../data/regions';
import { RootStackParamList } from '../navigation/types';

type Props = NativeStackScreenProps<RootStackParamList, 'Detail'>;

export default function DetailScreen({ route }: Props) {
  const { benefitId } = route.params;
  const benefit = BENEFITS.find((b) => b.id === benefitId);

  if (!benefit) {
    return (
      <SafeAreaView style={styles.safeArea}>
        <Text style={styles.notFound}>혜택 정보를 찾을 수 없습니다.</Text>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safeArea} edges={['bottom']}>
      <ScrollView contentContainerStyle={styles.container}>
        <Text style={styles.categoryTag}>{CATEGORY_LABELS[benefit.category]}</Text>
        <Text style={styles.title}>{benefit.name}</Text>
        <Text style={styles.agency}>{benefit.agency}</Text>
        {benefit.regions ? (
          <Text style={styles.regionNote}>
            대상 지역: {benefit.regions.map(regionName).join(', ')}
          </Text>
        ) : null}

        <View style={styles.section}>
          <Text style={styles.sectionLabel}>혜택 설명</Text>
          <Text style={styles.sectionText}>{benefit.detail}</Text>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionLabel}>신청 방법</Text>
          <Text style={styles.sectionText}>{benefit.applyMethod}</Text>
        </View>

        <Pressable style={styles.linkButton} onPress={() => Linking.openURL(benefit.link)}>
          <Text style={styles.linkButtonText}>공식 사이트 바로가기</Text>
        </Pressable>

        <Text style={styles.disclaimer}>
          ※ 이 정보는 참고용 요약입니다. 선정 기준과 지원 금액은 매년 바뀌므로, 신청 전 공식 사이트에서
          최신 공고를 반드시 확인하세요.
        </Text>
      </ScrollView>
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
  categoryTag: {
    alignSelf: 'flex-start',
    fontSize: 12,
    fontWeight: '700',
    color: '#2F6FED',
    backgroundColor: '#EEF3FF',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 10,
    overflow: 'hidden',
  },
  title: {
    fontSize: 24,
    fontWeight: '800',
    color: '#1D2433',
    marginTop: 12,
  },
  agency: {
    fontSize: 14,
    color: '#6B7383',
    marginTop: 6,
  },
  regionNote: {
    fontSize: 13,
    color: '#2F6FED',
    marginTop: 8,
    fontWeight: '600',
  },
  section: {
    marginTop: 24,
  },
  sectionLabel: {
    fontSize: 14,
    fontWeight: '700',
    color: '#1D2433',
    marginBottom: 8,
  },
  sectionText: {
    fontSize: 15,
    color: '#3A4356',
    lineHeight: 23,
  },
  linkButton: {
    backgroundColor: '#2F6FED',
    borderRadius: 14,
    paddingVertical: 16,
    alignItems: 'center',
    marginTop: 32,
  },
  linkButtonText: {
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
  notFound: {
    padding: 20,
    fontSize: 15,
    color: '#6B7383',
  },
});
