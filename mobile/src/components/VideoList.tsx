import React, { useState } from 'react';
import {
  View,
  Text,
  Image,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  Alert,
  Modal,
  TextInput,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as Clipboard from 'expo-clipboard';
import { Video, VideoUpdate } from '../services/videoService';
import { useAuth } from '../hooks/useAuth';

interface VideoListProps {
  videos: Video[];
  onDelete: (videoId: string) => Promise<void>;
  onUpdate: (videoId: string, updates: VideoUpdate) => Promise<void>;
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

interface EditModalProps {
  video: Video;
  visible: boolean;
  onClose: () => void;
  onSave: (updates: VideoUpdate) => Promise<void>;
}

const EditModal: React.FC<EditModalProps> = ({
  video,
  visible,
  onClose,
  onSave,
}) => {
  const [title, setTitle] = useState(video.title);
  const [description, setDescription] = useState(video.description || '');
  const [isSaving, setIsSaving] = useState(false);

  const handleSave = async () => {
    try {
      setIsSaving(true);
      await onSave({
        title,
        description: description || undefined,
      });
      onClose();
    } catch (error) {
      Alert.alert('Error', 'Failed to update video');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      transparent={true}
      onRequestClose={onClose}
    >
      <View style={styles.modalContainer}>
        <View style={styles.modalContent}>
          <Text style={styles.modalTitle}>Edit Video</Text>
          
          <TextInput
            style={styles.input}
            value={title}
            onChangeText={setTitle}
            placeholder="Title"
            placeholderTextColor="#999"
          />
          
          <TextInput
            style={[styles.input, styles.textArea]}
            value={description}
            onChangeText={setDescription}
            placeholder="Description (optional)"
            placeholderTextColor="#999"
            multiline
            numberOfLines={4}
          />
          
          <View style={styles.modalButtons}>
            <TouchableOpacity
              style={[styles.button, styles.cancelButton]}
              onPress={onClose}
              disabled={isSaving}
            >
              <Text style={styles.buttonText}>Cancel</Text>
            </TouchableOpacity>
            
            <TouchableOpacity
              style={[styles.button, styles.saveButton]}
              onPress={handleSave}
              disabled={isSaving}
            >
              <Text style={styles.buttonText}>
                {isSaving ? 'Saving...' : 'Save'}
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
};

const VideoItem: React.FC<{
  video: Video;
  onDelete: (videoId: string) => Promise<void>;
  onUpdate: (videoId: string, updates: VideoUpdate) => Promise<void>;
}> = ({ video, onDelete, onUpdate }) => {
  const [isEditing, setIsEditing] = useState(false);

  const handleCopyLink = async () => {
    await Clipboard.setStringAsync(video.url);
    Alert.alert('Success', 'Link copied to clipboard');
  };

  const handleDelete = async () => {
    Alert.alert(
      'Delete Video',
      'Are you sure you want to delete this video?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await onDelete(video.id);
            } catch (error) {
              Alert.alert('Error', 'Failed to delete video');
            }
          },
        },
      ]
    );
  };

  return (
    <>
      <View style={styles.videoItem}>
        <Image source={{ uri: video.thumbnail_url }} style={styles.thumbnail} />
        <View style={styles.content}>
          <Text style={styles.title} numberOfLines={2}>
            {video.title}
          </Text>
          <Text style={styles.platform}>{video.platform}</Text>
        </View>
        
        <TouchableOpacity
          onPress={() => setIsEditing(true)}
          style={styles.actionButton}
        >
          <Ionicons name="pencil" size={24} color="#007AFF" />
        </TouchableOpacity>
        
        <TouchableOpacity
          onPress={handleCopyLink}
          style={styles.actionButton}
        >
          <Ionicons name="copy-outline" size={24} color="#007AFF" />
        </TouchableOpacity>
        
        <TouchableOpacity
          onPress={handleDelete}
          style={styles.actionButton}
        >
          <Ionicons name="trash-outline" size={24} color="#FF3B30" />
        </TouchableOpacity>
      </View>

      <EditModal
        video={video}
        visible={isEditing}
        onClose={() => setIsEditing(false)}
        onSave={async (updates) => {
          await onUpdate(video.id, updates);
          setIsEditing(false);
        }}
      />
    </>
  );
};

const VideoList: React.FC<VideoListProps> = ({
  videos,
  onDelete,
  onUpdate,
  onRefresh,
  isRefreshing = false,
}) => {
  return (
    <FlatList
      data={videos}
      renderItem={({ item }) => (
        <VideoItem
          video={item}
          onDelete={onDelete}
          onUpdate={onUpdate}
        />
      )}
      keyExtractor={(item) => item.id}
      style={styles.list}
      refreshing={isRefreshing}
      onRefresh={onRefresh}
    />
  );
};

const styles = StyleSheet.create({
  list: {
    flex: 1,
  },
  videoItem: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    padding: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
    alignItems: 'center',
  },
  thumbnail: {
    width: 80,
    height: 45,
    borderRadius: 4,
  },
  content: {
    flex: 1,
    marginHorizontal: 12,
  },
  title: {
    fontSize: 16,
    fontWeight: '500',
  },
  platform: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  actionButton: {
    padding: 8,
  },
  modalContainer: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    padding: 20,
  },
  modalContent: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 20,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
    fontSize: 16,
  },
  textArea: {
    height: 100,
    textAlignVertical: 'top',
  },
  modalButtons: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    marginTop: 20,
  },
  button: {
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 8,
    marginLeft: 10,
  },
  cancelButton: {
    backgroundColor: '#ddd',
  },
  saveButton: {
    backgroundColor: '#007AFF',
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '500',
  },
});

export default VideoList; 
