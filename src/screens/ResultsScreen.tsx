import { NativeStackScreenProps } from '@react-navigation/native-stack';
import React, { useMemo } from 'react';
import { FlatList, Pressable, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { CATEGORY_LABELS } from '../data/labels';
import { regionName } from '../data/regions';
import { incomePercentForProfile, matchBenefits } from '../lib/matchBenefits';
import { RootStackParamList } from '../navigation/types';
import { Benefit } from '../types';

type Props = NativeStackScreenProps<RootStackParamList, 'Results'>;

export default function ResultsScreen({ route, navigation }: Props) {
  const { profile } = route.params;

  const results = useMemo(() => matchBenefits(profile), [profile]);
  const incomePercent = useMemo(() => incomePercentForProfile(profile), [profile]);

  function renderItem({ item }: { item: Benefit }) {
    return (
      <Pressable
        style={styles.card}
        onPress={() => navigation.navigate('Detail', { benefitId: item.id, profile })}
      >
        <View style={styles.cardTop}>
          <Text style={styles.categoryTag}>{CATEGORY_LABELS[item.category]}</Text>
          <Text style={styles.chevron}>›</Text>
        </View>
        <Text style={styles.cardTitle}>{item.name}</Text>
        <Text style={styles.cardSummary}>{item.summary}</Text>
        <Text style={styles.cardAgency}>{item.agency}</Text>
      </Pressable>
    );
  }

  return (
    <SafeAreaView style={styles.safeArea} edges={['bottom']}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>
          {regionName(profile.region)} · {profile.age}세 · {profile.householdSize}인 가구
        </Text>
        <Text style={styles.headerSubtitle}>
          소득 기준 중위소득 약 {incomePercent}% 수준 (참고용) · 총 {results.length}건 매칭
        </Text>
      </View>

      {results.length === 0 ? (
        <View style={styles.emptyWrap}>
          <Text style={styles.emptyTitle}>조건에 맞는 혜택을 찾지 못했어요</Text>
          <Text style={styles.emptyText}>
            입력하신 정보 기준으로 매칭되는 항목이 없습니다.{'\n'}
            정보를 다시 확인하거나 복지로에서 전체 목록을 확인해보세요.
          </Text>
        </View>
      ) : (
        <FlatList
          data={results}
          keyExtractor={(item) => item.id}
          renderItem={renderItem}
          contentContainerStyle={styles.listContent}
        />
      )}

      <Pressable style={styles.editButton} onPress={() => navigation.goBack()}>
        <Text style={styles.editButtonText}>정보 다시 입력하기</Text>
      </Pressable>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#F5F7FB',
  },
  header: {
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 8,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: '#1D2433',
  },
  headerSubtitle: {
    marginTop: 4,
    fontSize: 13,
    color: '#6B7383',
  },
  listContent: {
    padding: 20,
    paddingTop: 8,
    paddingBottom: 16,
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#EEF1F6',
  },
  cardTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  categoryTag: {
    fontSize: 12,
    fontWeight: '700',
    color: '#2F6FED',
    backgroundColor: '#EEF3FF',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 10,
    overflow: 'hidden',
  },
  chevron: {
    fontSize: 20,
    color: '#C4CAD4',
  },
  cardTitle: {
    fontSize: 17,
    fontWeight: '700',
    color: '#1D2433',
    marginTop: 10,
  },
  cardSummary: {
    fontSize: 14,
    color: '#565F70',
    marginTop: 6,
    lineHeight: 20,
  },
  cardAgency: {
    fontSize: 12,
    color: '#9AA3B2',
    marginTop: 10,
  },
  emptyWrap: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 32,
  },
  emptyTitle: {
    fontSize: 17,
    fontWeight: '700',
    color: '#1D2433',
    marginBottom: 8,
  },
  emptyText: {
    fontSize: 14,
    color: '#6B7383',
    textAlign: 'center',
    lineHeight: 21,
  },
  editButton: {
    marginHorizontal: 20,
    marginBottom: 16,
    paddingVertical: 14,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#D8DEE9',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
  },
  editButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#2F6FED',
  },
});
