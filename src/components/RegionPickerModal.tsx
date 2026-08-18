import React from 'react';
import { FlatList, Modal, Pressable, SafeAreaView, StyleSheet, Text, View } from 'react-native';
import { REGIONS } from '../data/regions';
import { RegionCode } from '../types';

interface RegionPickerModalProps {
  visible: boolean;
  selected: RegionCode | null;
  onSelect: (code: RegionCode) => void;
  onClose: () => void;
}

export function RegionPickerModal({ visible, selected, onSelect, onClose }: RegionPickerModalProps) {
  return (
    <Modal visible={visible} animationType="slide" transparent onRequestClose={onClose}>
      <View style={styles.overlay}>
        <SafeAreaView style={styles.sheet}>
          <View style={styles.header}>
            <Text style={styles.title}>거주 지역 선택</Text>
            <Pressable onPress={onClose} hitSlop={12}>
              <Text style={styles.close}>닫기</Text>
            </Pressable>
          </View>
          <FlatList
            data={REGIONS}
            keyExtractor={(item) => item.code}
            renderItem={({ item }) => (
              <Pressable
                style={[styles.row, selected === item.code && styles.rowSelected]}
                onPress={() => {
                  onSelect(item.code);
                  onClose();
                }}
              >
                <Text style={[styles.rowText, selected === item.code && styles.rowTextSelected]}>
                  {item.name}
                </Text>
              </Pressable>
            )}
          />
        </SafeAreaView>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.4)',
    justifyContent: 'flex-end',
  },
  sheet: {
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '75%',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#EEF1F6',
  },
  title: {
    fontSize: 17,
    fontWeight: '700',
    color: '#1D2433',
  },
  close: {
    fontSize: 15,
    color: '#2F6FED',
    fontWeight: '600',
  },
  row: {
    paddingHorizontal: 20,
    paddingVertical: 14,
  },
  rowSelected: {
    backgroundColor: '#EEF3FF',
  },
  rowText: {
    fontSize: 16,
    color: '#1D2433',
  },
  rowTextSelected: {
    color: '#2F6FED',
    fontWeight: '700',
  },
});
