import React from 'react';
import { View, StyleSheet, FlatList } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import SearchBar from '../../components/SearchBar';
import VideoList from '../../components/VideoList';
import PlatformFilter from '../../components/PlatformFilter';

const HomeScreen = () => {
  const [searchQuery, setSearchQuery] = React.useState('');
  const [selectedPlatform, setSelectedPlatform] = React.useState('all');

  return (
    <SafeAreaView style={styles.container}>
      <SearchBar 
        value={searchQuery}
        onChangeText={setSearchQuery}
        onSearch={() => {/* TODO: Implement search */}}
      />
      
      <PlatformFilter
        selected={selectedPlatform}
        onSelect={setSelectedPlatform}
      />

      <VideoList 
        platform={selectedPlatform}
        searchQuery={searchQuery}
      />
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
});

export default HomeScreen; 