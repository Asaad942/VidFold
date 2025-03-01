import { Stack } from 'expo-router';
import React from 'react';

export default function SettingsLayout() {
  return (
    <Stack>
      <Stack.Screen
        name="edit-profile"
        options={{
          title: 'Edit Profile',
          presentation: 'modal',
        }}
      />
      <Stack.Screen
        name="manage-videos"
        options={{
          title: 'Manage Videos',
        }}
      />
      <Stack.Screen
        name="privacy-policy"
        options={{
          title: 'Privacy Policy',
        }}
      />
      <Stack.Screen
        name="faqs"
        options={{
          title: 'FAQs',
        }}
      />
    </Stack>
  );
} 