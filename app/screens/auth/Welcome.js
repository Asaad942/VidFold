import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Button } from '@rneui/themed';
import { SafeAreaView } from 'react-native-safe-area-context';

export default function Welcome({ navigation }) {
  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>Welcome to VidFold</Text>
        <Text style={styles.subtitle}>Never lose a saved video again</Text>
        
        <View style={styles.buttonContainer}>
          <Button
            title="Sign Up"
            buttonStyle={styles.signUpButton}
            onPress={() => navigation.navigate('SignUp')}
          />
          <Button
            title="Login"
            type="outline"
            buttonStyle={styles.loginButton}
            onPress={() => navigation.navigate('Login')}
          />
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    marginBottom: 10,
    color: '#000',
  },
  subtitle: {
    fontSize: 18,
    color: '#666',
    marginBottom: 40,
    textAlign: 'center',
  },
  buttonContainer: {
    width: '100%',
    gap: 15,
  },
  signUpButton: {
    backgroundColor: '#2089dc',
    borderRadius: 10,
    padding: 15,
  },
  loginButton: {
    borderRadius: 10,
    padding: 15,
    borderColor: '#2089dc',
    borderWidth: 2,
  },
}); 