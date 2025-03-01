import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Image, ScrollView, Alert } from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { router } from 'expo-router';

import { Colors } from '@/constants/Colors';
import { IconSymbol } from '@/components/ui/IconSymbol';

interface ProfileOption {
  icon: string;
  title: string;
  onPress: () => void;
}

export default function ProfileScreen() {
  const [avatar, setAvatar] = useState<string | null>(null);
  const [username, setUsername] = useState('John Doe'); // TODO: Get from auth state

  const handlePickImage = async () => {
    const permissionResult = await ImagePicker.requestMediaLibraryPermissionsAsync();
    
    if (permissionResult.granted === false) {
      Alert.alert('Permission Required', 'Please allow access to your photo library to change profile picture.');
      return;
    }

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [1, 1],
      quality: 0.5,
    });

    if (!result.canceled) {
      setAvatar(result.assets[0].uri);
      // TODO: Upload avatar to backend
    }
  };

  const handleEditProfile = () => {
    router.push('/modal/edit-profile');
  };

  const handleManageVideos = () => {
    router.push('/modal/manage-videos');
  };

  const handlePrivacyPolicy = () => {
    router.push('/modal/privacy-policy');
  };

  const handleFAQs = () => {
    router.push('/modal/faqs');
  };

  const handleLogout = () => {
    Alert.alert(
      'Logout',
      'Are you sure you want to logout?',
      [
        {
          text: 'Cancel',
          style: 'cancel',
        },
        {
          text: 'Logout',
          style: 'destructive',
          onPress: () => {
            // TODO: Implement logout logic
            router.replace('/');
          },
        },
      ],
    );
  };

  const options: ProfileOption[] = [
    {
      icon: 'person.circle',
      title: 'Edit Profile',
      onPress: handleEditProfile,
    },
    {
      icon: 'film.stack',
      title: 'Manage Videos',
      onPress: handleManageVideos,
    },
    {
      icon: 'shield',
      title: 'Privacy Policy',
      onPress: handlePrivacyPolicy,
    },
    {
      icon: 'questionmark.circle',
      title: 'FAQs',
      onPress: handleFAQs,
    },
    {
      icon: 'rectangle.portrait.and.arrow.right',
      title: 'Logout',
      onPress: handleLogout,
    },
  ];

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={handlePickImage} style={styles.avatarContainer}>
          {avatar ? (
            <Image source={{ uri: avatar }} style={styles.avatar} />
          ) : (
            <View style={styles.avatarPlaceholder}>
              <IconSymbol name="person.circle.fill" size={60} color="#666" />
            </View>
          )}
          <View style={styles.editAvatarButton}>
            <IconSymbol name="camera.fill" size={12} color="#fff" />
          </View>
        </TouchableOpacity>
        <Text style={styles.username}>{username}</Text>
      </View>

      <View style={styles.optionsContainer}>
        {options.map((option, index) => (
          <TouchableOpacity
            key={option.title}
            style={[
              styles.option,
              index !== options.length - 1 && styles.optionBorder,
            ]}
            onPress={option.onPress}
          >
            <View style={styles.optionContent}>
              <IconSymbol name={option.icon} size={24} color={Colors.light.tint} />
              <Text style={styles.optionText}>{option.title}</Text>
            </View>
            <IconSymbol name="chevron.right" size={20} color="#666" />
          </TouchableOpacity>
        ))}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  header: {
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  avatarContainer: {
    width: 100,
    height: 100,
    borderRadius: 50,
    marginBottom: 10,
  },
  avatar: {
    width: '100%',
    height: '100%',
    borderRadius: 50,
  },
  avatarPlaceholder: {
    width: '100%',
    height: '100%',
    borderRadius: 50,
    backgroundColor: '#f0f0f0',
    justifyContent: 'center',
    alignItems: 'center',
  },
  editAvatarButton: {
    position: 'absolute',
    right: 0,
    bottom: 0,
    backgroundColor: Colors.light.tint,
    width: 24,
    height: 24,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#fff',
  },
  username: {
    fontSize: 20,
    fontWeight: '600',
    color: '#333',
  },
  optionsContainer: {
    marginTop: 20,
  },
  option: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 15,
    backgroundColor: '#fff',
  },
  optionContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  optionText: {
    fontSize: 16,
    marginLeft: 15,
    color: '#333',
  },
  optionBorder: {
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
}); 