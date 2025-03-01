import React, { useState } from 'react';
import { View, Text, StyleSheet, FlatList, TouchableOpacity, Alert } from 'react-native';
import { IconSymbol } from '@/components/ui/IconSymbol';
import { Colors } from '@/constants/Colors';

interface Video {
  id: string;
  title: string;
  platform: string;
  thumbnail?: string;
}

export default function ManageVideosScreen() {
  const [videos, setVideos] = useState<Video[]>([
    // TODO: Fetch from backend
    {
      id: '1',
      title: 'How to make a delicious cake',
      platform: 'YouTube',
    },
    {
      id: '2',
      title: 'Amazing dance moves tutorial',
      platform: 'Instagram',
    },
  ]);

  const [selectedVideos, setSelectedVideos] = useState<Set<string>>(new Set());

  const toggleVideoSelection = (id: string) => {
    const newSelection = new Set(selectedVideos);
    if (newSelection.has(id)) {
      newSelection.delete(id);
    } else {
      newSelection.add(id);
    }
    setSelectedVideos(newSelection);
  };

  const handleDeleteSelected = () => {
    if (selectedVideos.size === 0) return;

    Alert.alert(
      'Delete Videos',
      `Are you sure you want to delete ${selectedVideos.size} video${selectedVideos.size > 1 ? 's' : ''}?`,
      [
        {
          text: 'Cancel',
          style: 'cancel',
        },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              // TODO: Implement delete logic
              // await deleteVideos(Array.from(selectedVideos));
              setVideos(videos.filter(video => !selectedVideos.has(video.id)));
              setSelectedVideos(new Set());
            } catch (error) {
              Alert.alert('Error', 'Failed to delete videos');
            }
          },
        },
      ],
    );
  };

  const renderVideo = ({ item }: { item: Video }) => {
    const isSelected = selectedVideos.has(item.id);

    return (
      <TouchableOpacity
        style={[styles.videoItem, isSelected && styles.videoItemSelected]}
        onPress={() => toggleVideoSelection(item.id)}
      >
        <View style={styles.videoInfo}>
          <IconSymbol
            name={isSelected ? 'checkmark.circle.fill' : 'circle'}
            size={24}
            color={isSelected ? Colors.light.tint : '#666'}
          />
          <View style={styles.videoTextContainer}>
            <Text style={styles.videoTitle} numberOfLines={1}>
              {item.title}
            </Text>
            <Text style={styles.videoPlatform}>{item.platform}</Text>
          </View>
        </View>
      </TouchableOpacity>
    );
  };

  return (
    <View style={styles.container}>
      {videos.length > 0 ? (
        <>
          <FlatList
            data={videos}
            renderItem={renderVideo}
            keyExtractor={item => item.id}
            contentContainerStyle={styles.listContent}
          />
          {selectedVideos.size > 0 && (
            <TouchableOpacity
              style={styles.deleteButton}
              onPress={handleDeleteSelected}
            >
              <IconSymbol name="trash" size={20} color="#fff" />
              <Text style={styles.deleteButtonText}>
                Delete Selected ({selectedVideos.size})
              </Text>
            </TouchableOpacity>
          )}
        </>
      ) : (
        <View style={styles.emptyContainer}>
          <IconSymbol name="film" size={48} color="#666" />
          <Text style={styles.emptyText}>No videos saved yet</Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  listContent: {
    padding: 20,
  },
  videoItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 15,
    backgroundColor: '#fff',
    borderRadius: 8,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#eee',
  },
  videoItemSelected: {
    backgroundColor: '#f0f9ff',
    borderColor: Colors.light.tint,
  },
  videoInfo: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
  },
  videoTextContainer: {
    marginLeft: 12,
    flex: 1,
  },
  videoTitle: {
    fontSize: 16,
    fontWeight: '500',
    color: '#333',
  },
  videoPlatform: {
    fontSize: 14,
    color: '#666',
    marginTop: 2,
  },
  deleteButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#dc2626',
    margin: 20,
    padding: 15,
    borderRadius: 8,
  },
  deleteButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
    marginLeft: 8,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  emptyText: {
    fontSize: 16,
    color: '#666',
    marginTop: 12,
  },
}); 