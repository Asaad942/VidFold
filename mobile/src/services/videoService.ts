import { API_URL } from '../constants/config';

export interface Video {
  id: string;
  title: string;
  description?: string;
  url: string;
  thumbnail_url: string;
  platform: string;
  created_at: string;
  keywords: string[];
}

export interface VideoUpdate {
  title?: string;
  description?: string;
  keywords?: string[];
}

export interface VideosResponse {
  videos: Video[];
  total: number;
  limit: number;
  offset: number;
}

export const getVideos = async (
  token: string,
  platform?: string,
  limit: number = 50,
  offset: number = 0
): Promise<VideosResponse> => {
  const params = new URLSearchParams({
    limit: limit.toString(),
    offset: offset.toString(),
  });
  
  if (platform) {
    params.append('platform', platform);
  }
  
  const response = await fetch(
    `${API_URL}/videos?${params.toString()}`,
    {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    throw new Error('Failed to fetch videos');
  }

  return response.json();
};

export const updateVideo = async (
  videoId: string,
  updates: VideoUpdate,
  token: string
): Promise<Video> => {
  const response = await fetch(
    `${API_URL}/videos/${videoId}`,
    {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(updates),
    }
  );

  if (!response.ok) {
    throw new Error('Failed to update video');
  }

  return response.json();
};

export const deleteVideo = async (
  videoId: string,
  token: string
): Promise<void> => {
  const response = await fetch(
    `${API_URL}/videos/${videoId}`,
    {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    throw new Error('Failed to delete video');
  }
}; 