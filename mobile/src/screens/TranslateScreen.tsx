import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ScrollView,
  ActivityIndicator,
} from 'react-native';
import { apiService } from '../services/ApiService';

export const TranslateScreen = () => {
  const [inputText, setInputText] = useState('');
  const [translatedText, setTranslatedText] = useState('');
  const [targetLang, setTargetLang] = useState('en');
  const [sourceLang, setSourceLang] = useState('auto');
  const [isLoading, setIsLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    checkConnection();
  }, []);

  const checkConnection = async () => {
    try {
      await apiService.healthCheck();
      setIsConnected(true);
    } catch (error) {
      setIsConnected(false);
      Alert.alert('Connection Error', 'Cannot connect to translation service');
    }
  };

  const handleTranslate = async () => {
    if (!inputText.trim()) {
      Alert.alert('Error', 'Please enter text to translate');
      return;
    }

    setIsLoading(true);
    try {
      const result = await apiService.translate(inputText, targetLang, sourceLang);
      setTranslatedText(result.translated_text || result.text);
    } catch (error) {
      Alert.alert('Translation Error', error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const swapLanguages = () => {
    if (sourceLang !== 'auto') {
      setSourceLang(targetLang);
      setTargetLang(sourceLang);
      setInputText(translatedText);
      setTranslatedText(inputText);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>LLMyTranslate</Text>
        <View style={[styles.statusIndicator, { backgroundColor: isConnected ? '#4CAF50' : '#F44336' }]} />
      </View>

      <View style={styles.languageSelector}>
        <TouchableOpacity style={styles.langButton}>
          <Text style={styles.langText}>{sourceLang === 'auto' ? 'Auto' : sourceLang.toUpperCase()}</Text>
        </TouchableOpacity>
        
        <TouchableOpacity onPress={swapLanguages} style={styles.swapButton}>
          <Text style={styles.swapText}>⇄</Text>
        </TouchableOpacity>
        
        <TouchableOpacity style={styles.langButton}>
          <Text style={styles.langText}>{targetLang.toUpperCase()}</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.inputSection}>
        <Text style={styles.sectionTitle}>Enter Text</Text>
        <TextInput
          style={styles.textInput}
          value={inputText}
          onChangeText={setInputText}
          placeholder="Type text to translate..."
          multiline
          numberOfLines={4}
        />
      </View>

      <TouchableOpacity
        style={[styles.translateButton, { backgroundColor: isLoading ? '#ccc' : '#2196F3' }]}
        onPress={handleTranslate}
        disabled={isLoading}
      >
        {isLoading ? (
          <ActivityIndicator color="white" />
        ) : (
          <Text style={styles.buttonText}>Translate</Text>
        )}
      </TouchableOpacity>

      {translatedText ? (
        <View style={styles.outputSection}>
          <Text style={styles.sectionTitle}>Translation</Text>
          <View style={styles.translationOutput}>
            <Text style={styles.translatedText}>{translatedText}</Text>
          </View>
        </View>
      ) : null}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    padding: 16,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 24,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  statusIndicator: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  languageSelector: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 24,
  },
  langButton: {
    backgroundColor: '#e0e0e0',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
    minWidth: 80,
    alignItems: 'center',
  },
  langText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
  },
  swapButton: {
    padding: 8,
  },
  swapText: {
    fontSize: 24,
    color: '#2196F3',
  },
  inputSection: {
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 8,
    color: '#333',
  },
  textInput: {
    backgroundColor: 'white',
    borderRadius: 8,
    padding: 16,
    fontSize: 16,
    textAlignVertical: 'top',
    minHeight: 100,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  translateButton: {
    backgroundColor: '#2196F3',
    paddingVertical: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: 24,
  },
  buttonText: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
  },
  outputSection: {
    marginBottom: 24,
  },
  translationOutput: {
    backgroundColor: 'white',
    borderRadius: 8,
    padding: 16,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  translatedText: {
    fontSize: 16,
    lineHeight: 24,
    color: '#333',
  },
});
