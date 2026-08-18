import React from 'react';
import { StyleSheet, Text, TextInput, View } from 'react-native';

interface NumberFieldProps {
  label: string;
  value: number;
  onChange: (value: number) => void;
  suffix?: string;
  placeholder?: string;
  helperText?: string;
}

export function NumberField({ label, value, onChange, suffix, placeholder, helperText }: NumberFieldProps) {
  return (
    <View style={styles.container}>
      <Text style={styles.label}>{label}</Text>
      <View style={styles.inputRow}>
        <TextInput
          style={styles.input}
          keyboardType="number-pad"
          inputMode="numeric"
          value={value === 0 ? '' : String(value)}
          onChangeText={(text) => {
            const digitsOnly = text.replace(/[^0-9]/g, '');
            onChange(digitsOnly === '' ? 0 : parseInt(digitsOnly, 10));
          }}
          placeholder={placeholder}
          placeholderTextColor="#9AA3B2"
        />
        {suffix ? <Text style={styles.suffix}>{suffix}</Text> : null}
      </View>
      {helperText ? <Text style={styles.helper}>{helperText}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: 20,
  },
  label: {
    fontSize: 15,
    fontWeight: '600',
    color: '#1D2433',
    marginBottom: 8,
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#D8DEE9',
    borderRadius: 12,
    paddingHorizontal: 14,
    backgroundColor: '#FFFFFF',
  },
  input: {
    flex: 1,
    paddingVertical: 12,
    fontSize: 16,
    color: '#1D2433',
  },
  suffix: {
    fontSize: 15,
    color: '#6B7383',
    marginLeft: 8,
  },
  helper: {
    marginTop: 6,
    fontSize: 12,
    color: '#8A93A3',
  },
});
