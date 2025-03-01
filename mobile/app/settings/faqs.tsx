import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Animated } from 'react-native';
import { IconSymbol } from '@/components/ui/IconSymbol';
import { Colors } from '@/constants/Colors';

interface FAQ {
  question: string;
  answer: string;
}

const faqs: FAQ[] = [
  {
    question: 'How do I save a video?',
    answer: 'You can save a video in two ways:\n1. Copy the video link and paste it in the Add Video page\n2. Use the share button in apps like YouTube, Instagram, TikTok, or Facebook and select VidFold',
  },
  {
    question: 'What video platforms are supported?',
    answer: 'We currently support videos from:\n• YouTube\n• Instagram\n• TikTok\n• Facebook',
  },
  {
    question: 'How does the search work?',
    answer: 'Our AI analyzes the video content, including:\n• Visual content\n• Audio transcription\n• Title and description\n\nYou can search using natural language, describing what you remember about the video.',
  },
  {
    question: 'Can I organize videos into categories?',
    answer: 'Yes! When saving a video, you can add it to one or more categories. You can also manage categories later from the video management screen.',
  },
  {
    question: 'Is my data secure?',
    answer: 'Yes, we take security seriously. Your data is encrypted and stored securely. We only store the necessary information to provide our service and never share your data with third parties.',
  },
  {
    question: 'How do I delete my account?',
    answer: 'You can delete your account and all associated data from the Edit Profile screen. This action is permanent and cannot be undone.',
  },
];

function FAQItem({ faq }: { faq: FAQ }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [animation] = useState(new Animated.Value(0));

  const toggleExpand = () => {
    const toValue = isExpanded ? 0 : 1;
    Animated.spring(animation, {
      toValue,
      useNativeDriver: true,
    }).start();
    setIsExpanded(!isExpanded);
  };

  const rotateIcon = animation.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '90deg'],
  });

  return (
    <View style={styles.faqItem}>
      <TouchableOpacity
        style={styles.questionContainer}
        onPress={toggleExpand}
        activeOpacity={0.7}
      >
        <Text style={styles.question}>{faq.question}</Text>
        <Animated.View style={{ transform: [{ rotate: rotateIcon }] }}>
          <IconSymbol
            name="chevron.right"
            size={20}
            color="#666"
          />
        </Animated.View>
      </TouchableOpacity>
      {isExpanded && (
        <Text style={styles.answer}>{faq.answer}</Text>
      )}
    </View>
  );
}

export default function FAQsScreen() {
  return (
    <ScrollView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>Frequently Asked Questions</Text>
        {faqs.map((faq, index) => (
          <FAQItem key={index} faq={faq} />
        ))}
        <View style={styles.helpSection}>
          <Text style={styles.helpText}>
            Still have questions? Contact us at:
          </Text>
          <Text style={styles.helpEmail}>support@vidfold.com</Text>
        </View>
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
  faqItem: {
    marginBottom: 15,
    borderWidth: 1,
    borderColor: '#eee',
    borderRadius: 8,
    overflow: 'hidden',
  },
  questionContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 15,
    backgroundColor: '#f8f8f8',
  },
  question: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    flex: 1,
    marginRight: 10,
  },
  answer: {
    fontSize: 16,
    lineHeight: 24,
    color: '#444',
    padding: 15,
    backgroundColor: '#fff',
  },
  helpSection: {
    marginTop: 30,
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#f8f8f8',
    borderRadius: 8,
  },
  helpText: {
    fontSize: 16,
    color: '#666',
    marginBottom: 8,
  },
  helpEmail: {
    fontSize: 16,
    color: Colors.light.tint,
    fontWeight: '500',
  },
}); 