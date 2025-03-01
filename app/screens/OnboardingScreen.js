import React, { useState } from 'react';
import {
  StyleSheet,
  View,
  Text,
  TouchableOpacity,
  Dimensions,
  SafeAreaView,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';

const { width } = Dimensions.get('window');

const onboardingQuestions = [
  {
    question: "Do you often lose track of your saved videos?",
    id: 1,
  },
  {
    question: "Is organizing content across platforms a hassle?",
    id: 2,
  },
  {
    question: "Want a simpler way to manage your video collection?",
    id: 3,
  },
];

const OnboardingScreen = ({ navigation }) => {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);

  const handleAnswer = (answer) => {
    if (currentQuestionIndex < onboardingQuestions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    } else {
      // Navigate to the main app after completing onboarding
      navigation.replace('MainApp');
    }
  };

  const currentQuestion = onboardingQuestions[currentQuestionIndex];

  return (
    <LinearGradient
      colors={['#4A90E2', '#50E3C2']}
      style={styles.container}
    >
      <SafeAreaView style={styles.container}>
        <View style={styles.content}>
          <Text style={styles.stepIndicator}>
            Step {currentQuestionIndex + 1} of {onboardingQuestions.length}
          </Text>
          
          <View style={styles.questionContainer}>
            <Text style={styles.questionText}>
              {currentQuestion.question}
            </Text>
          </View>

          <View style={styles.buttonsContainer}>
            <TouchableOpacity
              style={[styles.button, styles.yesButton]}
              onPress={() => handleAnswer(true)}
            >
              <Text style={styles.buttonText}>Yes</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.button, styles.noButton]}
              onPress={() => handleAnswer(false)}
            >
              <Text style={styles.buttonText}>No</Text>
            </TouchableOpacity>
          </View>

          <View style={styles.progressDots}>
            {onboardingQuestions.map((_, index) => (
              <View
                key={index}
                style={[
                  styles.dot,
                  index === currentQuestionIndex && styles.activeDot,
                ]}
              />
            ))}
          </View>
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
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  stepIndicator: {
    color: '#FFFFFF',
    fontSize: 16,
    marginBottom: 40,
    opacity: 0.8,
  },
  questionContainer: {
    alignItems: 'center',
    marginBottom: 40,
  },
  questionText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#FFFFFF',
    textAlign: 'center',
    lineHeight: 32,
  },
  buttonsContainer: {
    width: '100%',
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    marginBottom: 40,
  },
  button: {
    width: width * 0.4,
    padding: 15,
    borderRadius: 25,
    alignItems: 'center',
  },
  yesButton: {
    backgroundColor: '#FFFFFF',
  },
  noButton: {
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
  },
  buttonText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#4A90E2',
  },
  progressDots: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
    marginHorizontal: 4,
  },
  activeDot: {
    backgroundColor: '#FFFFFF',
    transform: [{ scale: 1.2 }],
  },
});

export default OnboardingScreen; 