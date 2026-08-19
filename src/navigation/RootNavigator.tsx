import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import React from 'react';
import DetailScreen from '../screens/DetailScreen';
import InputScreen from '../screens/InputScreen';
import ResultsScreen from '../screens/ResultsScreen';
import { RootStackParamList } from './types';

const Stack = createNativeStackNavigator<RootStackParamList>();

export default function RootNavigator() {
  return (
    <NavigationContainer>
      <Stack.Navigator
        screenOptions={{
          headerStyle: { backgroundColor: '#F5F7FB' },
          headerShadowVisible: false,
          headerTintColor: '#1D2433',
          headerTitleStyle: { fontWeight: '700' },
        }}
      >
        <Stack.Screen name="Input" component={InputScreen} options={{ title: '내 정보 입력' }} />
        <Stack.Screen name="Results" component={ResultsScreen} options={{ title: '맞춤 혜택' }} />
        <Stack.Screen name="Detail" component={DetailScreen} options={{ title: '혜택 상세' }} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
