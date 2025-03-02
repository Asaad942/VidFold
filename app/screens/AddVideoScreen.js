import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ScrollView,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { videoService } from '../services/videoService';
import { useNavigation } from '@react-navigation/native';

const categories = [
  'YouTube',
  'Instagram',
  'Facebook',
  'TikTok',
  'Twitter',
];

const AddVideoScreen = () => {
  const [videoUrl, setVideoUrl] = useState('');
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [loading, setLoading] = useState(false);
  const [processingStatus, setProcessingStatus] = useState('');
  const navigation = useNavigation();

  const detectPlatform = (url) => {
    const urlLower = url.toLowerCase();
    if (urlLower.includes('youtube.com') || urlLower.includes('youtu.be')) return 'YouTube';
    if (urlLower.includes('instagram.com')) return 'Instagram';
    if (urlLower.includes('facebook.com') || urlLower.includes('fb.watch')) return 'Facebook';
    if (urlLower.includes('tiktok.com')) return 'TikTok';
    if (urlLower.includes('twitter.com') || urlLower.includes('x.com')) return 'Twitter';
    return null;
  };

  const validateUrl = (url) => {
    try {
      new URL(url);
      return true;
    } catch (e) {
      return false;
    }
  };

  const handleAddVideo = async () => {
    if (!videoUrl.trim()) {
      Alert.alert('Error', 'Please enter a video URL');
      return;
    }

    if (!validateUrl(videoUrl)) {
      Alert.alert('Error', 'Please enter a valid URL');
      return;
    }

    const platform = selectedCategory || detectPlatform(videoUrl);
    if (!platform) {
      Alert.alert('Error', 'Please select a platform for this video');
      return;
    }

    setLoading(true);
    setProcessingStatus('Adding video...');
    try {
      const result = await videoService.addVideo(videoUrl, platform);
      
      // Show success message but don't block navigation
      Alert.alert(
        'Success',
        'Video added successfully! Processing will continue in the background.',
        [
          {
            text: 'View Videos',
            onPress: () => {
              setVideoUrl('');
              setSelectedCategory(null);
              navigation.navigate('HomeTab');
            },
          },
          {
            text: 'Add Another',
            onPress: () => {
              setVideoUrl('');
              setSelectedCategory(null);
              setProcessingStatus('');
            },
          }
        ],
        { cancelable: false }
      );
    } catch (error) {
      Alert.alert('Error', error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <LinearGradient
      colors={['#4A90E2', '#50E3C2']}
      style={styles.container}
    >
      <SafeAreaView style={styles.container}>
        <View style={styles.content}>
          <Text style={styles.title}>Add New Video</Text>
          
          <View style={styles.inputContainer}>
            <TextInput
              style={styles.input}
              placeholder="Paste video link here..."
              placeholderTextColor="rgba(255, 255, 255, 0.7)"
              value={videoUrl}
              onChangeText={(text) => {
                setVideoUrl(text);
                if (!selectedCategory) {
                  const detected = detectPlatform(text);
                  if (detected) setSelectedCategory(detected);
                }
              }}
              autoCapitalize="none"
              autoCorrect={false}
              editable={!loading}
            />
            <TouchableOpacity
              style={[styles.addButton, loading && styles.addButtonDisabled]}
              onPress={handleAddVideo}
              disabled={!videoUrl || loading}
            >
              {loading ? (
                <ActivityIndicator color="#4A90E2" size="small" />
              ) : (
                <Ionicons
                  name="add-circle"
                  size={32}
                  color={videoUrl ? '#4A90E2' : '#999999'}
                />
              )}
            </TouchableOpacity>
          </View>

          {processingStatus ? (
            <View style={styles.processingContainer}>
              <ActivityIndicator color="#FFFFFF" />
              <Text style={styles.processingText}>{processingStatus}</Text>
            </View>
          ) : null}

          <Text style={styles.categoryTitle}>Select Platform</Text>
          
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            style={styles.categoriesContainer}
          >
            {categories.map((category) => (
              <TouchableOpacity
                key={category}
                style={[
                  styles.categoryChip,
                  selectedCategory === category && styles.selectedCategory,
                ]}
                onPress={() => setSelectedCategory(category)}
                disabled={loading}
              >
                <Text
                  style={[
                    styles.categoryText,
                    selectedCategory === category && styles.selectedCategoryText,
                  ]}
                >
                  {category}
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>

          {videoUrl && !selectedCategory && (
            <Text style={styles.warningText}>
              Please select a platform for your video
            </Text>
          )}
        </View>
      </SafeAreaView>
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    flex: 1,
    padding: 20,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginBottom: 30,
    textAlign: 'center',
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    borderRadius: 25,
    paddingHorizontal: 20,
    marginBottom: 30,
  },
  input: {
    flex: 1,
    height: 50,
    color: '#FFFFFF',
    fontSize: 16,
  },
  addButton: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 5,
    width: 42,
    height: 42,
    justifyContent: 'center',
    alignItems: 'center',
  },
  addButtonDisabled: {
    opacity: 0.7,
  },
  processingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    padding: 10,
    borderRadius: 10,
  },
  processingText: {
    color: '#FFFFFF',
    marginLeft: 10,
    fontSize: 14,
  },
  categoryTitle: {
    fontSize: 16,
    color: '#FFFFFF',
    marginBottom: 15,
    opacity: 0.9,
  },
  categoriesContainer: {
    flexDirection: 'row',
    marginBottom: 20,
  },
  categoryChip: {
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 20,
    marginRight: 10,
  },
  selectedCategory: {
    backgroundColor: '#FFFFFF',
  },
  categoryText: {
    color: '#FFFFFF',
    fontSize: 14,
  },
  selectedCategoryText: {
    color: '#4A90E2',
  },
  warningText: {
    color: '#FFD700',
    fontSize: 14,
    textAlign: 'center',
    marginTop: 10,
  },
});

export default AddVideoScreen; 