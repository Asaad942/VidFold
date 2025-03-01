import React from 'react';
import { View, TouchableOpacity, Text, StyleSheet } from 'react-native';

export interface PlatformFilterProps {
  selectedPlatform: string | null;
  onSelectPlatform: (platform: string | null) => void;
}

const platforms = ['YouTube', 'Instagram', 'TikTok', 'Facebook'];

const PlatformFilter: React.FC<PlatformFilterProps> = ({
  selectedPlatform,
  onSelectPlatform,
}) => {
  return (
    <View style={styles.container}>
      <TouchableOpacity
        style={[
          styles.filterButton,
          !selectedPlatform && styles.selectedButton,
        ]}
        onPress={() => onSelectPlatform(null)}
      >
        <Text
          style={[
            styles.buttonText,
            !selectedPlatform && styles.selectedButtonText,
          ]}
        >
          All
        </Text>
      </TouchableOpacity>

      {platforms.map((platform) => (
        <TouchableOpacity
          key={platform}
          style={[
            styles.filterButton,
            selectedPlatform === platform && styles.selectedButton,
          ]}
          onPress={() => onSelectPlatform(platform)}
        >
          <Text
            style={[
              styles.buttonText,
              selectedPlatform === platform && styles.selectedButtonText,
            ]}
          >
            {platform}
          </Text>
        </TouchableOpacity>
      ))}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    paddingHorizontal: 10,
    paddingVertical: 8,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  filterButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    marginRight: 8,
    backgroundColor: '#f5f5f5',
  },
  selectedButton: {
    backgroundColor: '#007AFF',
  },
  buttonText: {
    fontSize: 14,
    color: '#666',
  },
  selectedButtonText: {
    color: '#fff',
  },
});

export default PlatformFilter; 
