import { Stack } from 'expo-router';
import React from 'react';

export default function ModalLayout() {
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
          presentation: 'modal',
        }}
      />
      <Stack.Screen
        name="privacy-policy"
        options={{
          title: 'Privacy Policy',
          presentation: 'modal',
        }}
      />
      <Stack.Screen
        name="faqs"
        options={{
          title: 'FAQs',
          presentation: 'modal',
        }}
      />
    </Stack>
  );
} 