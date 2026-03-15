import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Text } from 'react-native';

import RadarScreen from './screens/RadarScreen';
import IPInfoScreen from './screens/IPInfoScreen';
import DomainsScreen from './screens/DomainsScreen';

const Tab = createBottomTabNavigator();

const COLORS = {
  background: '#0a0e1a',
  phosphor: '#00ff41',
  tabBar: '#0d1224',
  tabBarBorder: '#1a2340',
  inactive: '#3a5a3a',
};

function TabIcon({ name, focused }) {
  const icons = {
    Radar: '📡',
    'IP Info': '🛡️',
    Domains: '🔒',
  };
  return (
    <Text style={{ fontSize: 20, opacity: focused ? 1 : 0.5 }}>
      {icons[name]}
    </Text>
  );
}

export default function App() {
  return (
    <NavigationContainer>
      <StatusBar style="light" />
      <Tab.Navigator
        screenOptions={({ route }) => ({
          tabBarIcon: ({ focused }) => (
            <TabIcon name={route.name} focused={focused} />
          ),
          tabBarActiveTintColor: COLORS.phosphor,
          tabBarInactiveTintColor: COLORS.inactive,
          tabBarStyle: {
            backgroundColor: COLORS.tabBar,
            borderTopColor: COLORS.tabBarBorder,
            borderTopWidth: 1,
            paddingBottom: 4,
            height: 60,
          },
          tabBarLabelStyle: {
            fontSize: 11,
            fontWeight: '600',
            letterSpacing: 0.5,
          },
          headerStyle: {
            backgroundColor: COLORS.background,
            borderBottomColor: COLORS.tabBarBorder,
            borderBottomWidth: 1,
          },
          headerTintColor: COLORS.phosphor,
          headerTitleStyle: {
            fontWeight: '700',
            letterSpacing: 1,
            fontSize: 16,
          },
        })}
      >
        <Tab.Screen
          name="Radar"
          component={RadarScreen}
          options={{ title: 'IP PROTECTION RADAR' }}
        />
        <Tab.Screen
          name="IP Info"
          component={IPInfoScreen}
          options={{ title: 'IP INFORMATION' }}
        />
        <Tab.Screen
          name="Domains"
          component={DomainsScreen}
          options={{ title: 'MASKED DOMAINS' }}
        />
      </Tab.Navigator>
    </NavigationContainer>
  );
}
