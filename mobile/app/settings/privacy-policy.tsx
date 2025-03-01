import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';

export default function PrivacyPolicyScreen() {
  return (
    <ScrollView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>Privacy Policy</Text>
        
        <Text style={styles.section}>1. Information We Collect</Text>
        <Text style={styles.text}>
          We collect information that you provide directly to us, including:
        </Text>
        <Text style={styles.bullet}>• Account information (email, username)</Text>
        <Text style={styles.bullet}>• Profile information (avatar)</Text>
        <Text style={styles.bullet}>• Video links you save</Text>
        <Text style={styles.bullet}>• Categories you create</Text>

        <Text style={styles.section}>2. How We Use Your Information</Text>
        <Text style={styles.text}>
          We use the information we collect to:
        </Text>
        <Text style={styles.bullet}>• Provide and maintain our services</Text>
        <Text style={styles.bullet}>• Process and organize your saved videos</Text>
        <Text style={styles.bullet}>• Improve our video analysis and search features</Text>
        <Text style={styles.bullet}>• Send you important updates about our service</Text>

        <Text style={styles.section}>3. Data Storage</Text>
        <Text style={styles.text}>
          Your data is stored securely in our cloud infrastructure. We use industry-standard security measures to protect your information.
        </Text>

        <Text style={styles.section}>4. Third-Party Services</Text>
        <Text style={styles.text}>
          We integrate with various video platforms (YouTube, Instagram, TikTok, Facebook) to analyze and organize your saved videos. We only access the content you explicitly share with us.
        </Text>

        <Text style={styles.section}>5. Your Rights</Text>
        <Text style={styles.text}>
          You have the right to:
        </Text>
        <Text style={styles.bullet}>• Access your personal data</Text>
        <Text style={styles.bullet}>• Correct inaccurate data</Text>
        <Text style={styles.bullet}>• Delete your account and data</Text>
        <Text style={styles.bullet}>• Export your data</Text>

        <Text style={styles.section}>6. Contact Us</Text>
        <Text style={styles.text}>
          If you have any questions about this Privacy Policy, please contact us at:
        </Text>
        <Text style={styles.contact}>support@vidfold.com</Text>

        <Text style={styles.footer}>
          Last updated: {new Date().toLocaleDateString()}
        </Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  content: {
    padding: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 20,
    color: '#333',
  },
  section: {
    fontSize: 18,
    fontWeight: '600',
    marginTop: 20,
    marginBottom: 10,
    color: '#333',
  },
  text: {
    fontSize: 16,
    lineHeight: 24,
    color: '#444',
    marginBottom: 10,
  },
  bullet: {
    fontSize: 16,
    lineHeight: 24,
    color: '#444',
    marginLeft: 10,
    marginBottom: 5,
  },
  contact: {
    fontSize: 16,
    color: '#0066cc',
    marginTop: 5,
    marginBottom: 20,
  },
  footer: {
    fontSize: 14,
    color: '#666',
    marginTop: 30,
    fontStyle: 'italic',
  },
}); 