import React, { useState } from 'react';
import { View, TextInput, StyleSheet, TouchableOpacity, Text, Alert } from 'react-native';
import * as Clipboard from 'expo-clipboard';
import { router } from 'expo-router';

import { Colors } from '@/constants/Colors';
import { IconSymbol } from '@/components/ui/IconSymbol';
import { CategorySelector } from '@/components/CategorySelector';

export default function AddVideoScreen() {
  const [videoUrl, setVideoUrl] = useState('');
  const [categories, setCategories] = useState<string[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);

  const handlePasteFromClipboard = async () => {
    const text = await Clipboard.getStringAsync();
    if (text) {
      // Extract URL from text if needed (in case it's embedded in other text)
      const urlMatch = text.match(/https?:\/\/[^\s]+/);
      if (urlMatch) {
        setVideoUrl(urlMatch[0]);
      } else {
        setVideoUrl(text);
      }
    }
  };

  const handleAddVideo = async () => {
    if (!videoUrl) return;
    
    setIsProcessing(true);
    try {
      // TODO: Replace with your actual backend URL
      const response = await fetch('YOUR_BACKEND_URL/api/videos', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: videoUrl,
          categories: categories,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to process video');
      }

      // Navigate back to home on success
      router.push('/');
    } catch (error) {
      console.error('Error adding video:', error);
      Alert.alert(
        'Error',
        'Failed to add video. Please try again.',
        [{ text: 'OK' }]
      );
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.inputContainer}>
        <TextInput
          style={styles.input}
          value={videoUrl}
          onChangeText={setVideoUrl}
          placeholder="Paste video URL here"
          placeholderTextColor="#666"
          autoCapitalize="none"
          autoCorrect={false}
        />
        <TouchableOpacity onPress={handlePasteFromClipboard} style={styles.pasteButton}>
          <IconSymbol name="doc.on.clipboard" size={24} color={Colors.light.tint} />
        </TouchableOpacity>
      </View>

      <CategorySelector
        selectedCategories={categories}
        onCategoriesChange={setCategories}
      />
      
      <TouchableOpacity 
        style={[styles.addButton, !videoUrl && styles.addButtonDisabled]}
        onPress={handleAddVideo}
        disabled={!videoUrl || isProcessing}
      >
        <Text style={styles.addButtonText}>
          {isProcessing ? 'Processing...' : 'Add Video'}
        </Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    backgroundColor: '#fff',
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  input: {
    flex: 1,
    height: 50,
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    paddingHorizontal: 15,
    marginRight: 10,
    fontSize: 16,
  },
  pasteButton: {
    padding: 10,
  },
  addButton: {
    backgroundColor: Colors.light.tint,
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
  },
  addButtonDisabled: {
    opacity: 0.5,
  },
  addButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
}); 