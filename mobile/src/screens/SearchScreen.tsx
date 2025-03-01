import React, { useState, useCallback } from 'react';
import { View, StyleSheet, FlatList, ActivityIndicator, Text } from 'react-native';
import { useAuth } from '../hooks/useAuth';
import SearchBar from '../components/SearchBar';
import PlatformFilter from '../components/PlatformFilter';
import VideoList from '../components/VideoList';
import { searchVideos, SearchResult } from '../services/searchService';
import { debounce } from 'lodash';

export default function SearchScreen() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedPlatform, setSelectedPlatform] = useState<string | null>(null);
  const { token } = useAuth();

  const performSearch = useCallback(
    debounce(async (searchQuery: string) => {
      if (!searchQuery.trim()) {
        setResults([]);
        return;
      }

      try {
        setLoading(true);
        setError(null);
        const searchResults = await searchVideos(
          searchQuery,
          selectedPlatform,
          token
        );
        setResults(searchResults);
      } catch (err) {
        setError('Failed to search videos. Please try again.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    }, 300),
    [selectedPlatform, token]
  );

  const handleSearch = useCallback(() => {
    performSearch(query);
  }, [query, performSearch]);

  const handleQueryChange = (text: string) => {
    setQuery(text);
    performSearch(text);
  };

  return (
    <View style={styles.container}>
      <SearchBar
        value={query}
        onChangeText={handleQueryChange}
        onSearch={handleSearch}
      />
      
      <PlatformFilter
        selectedPlatform={selectedPlatform}
        onSelectPlatform={setSelectedPlatform}
      />

      {loading && (
        <View style={styles.centerContainer}>
          <ActivityIndicator size="large" color="#007AFF" />
        </View>
      )}

      {error && (
        <View style={styles.centerContainer}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      )}

      {!loading && !error && results.length === 0 && query.trim() !== '' && (
        <View style={styles.centerContainer}>
          <Text style={styles.noResultsText}>No videos found</Text>
        </View>
      )}

      {!loading && !error && results.length > 0 && (
        <VideoList videos={results} />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  errorText: {
    color: 'red',
    textAlign: 'center',
    marginHorizontal: 20,
  },
  noResultsText: {
    color: '#666',
    textAlign: 'center',
  },
}); 