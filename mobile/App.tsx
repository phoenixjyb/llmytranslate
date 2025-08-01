import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { TranslateScreen } from './src/screens/TranslateScreen';
import { ChatScreen } from './src/screens/ChatScreen';

const Tab = createBottomTabNavigator();

const App = () => {
  return (
    <NavigationContainer>
      <Tab.Navigator
        screenOptions={{
          tabBarActiveTintColor: '#2196F3',
          tabBarInactiveTintColor: '#666',
          headerStyle: {
            backgroundColor: '#2196F3',
          },
          headerTintColor: 'white',
          headerTitleStyle: {
            fontWeight: 'bold',
          },
        }}
      >
        <Tab.Screen 
          name="Translate" 
          component={TranslateScreen}
          options={{
            title: 'Translate',
            headerTitle: 'LLMyTranslate',
          }}
        />
        <Tab.Screen 
          name="Chat" 
          component={ChatScreen}
          options={{
            title: 'Chat',
            headerTitle: 'AI Chat',
          }}
        />
      </Tab.Navigator>
    </NavigationContainer>
  );
};

export default App;
