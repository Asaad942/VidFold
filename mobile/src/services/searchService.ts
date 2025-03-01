import { API_URL } from '../constants/config';

export interface SearchResult {
  id: string;
  title: string;
  url: string;
  thumbnail_url: string;
  platform: string;
  relevance_score: number;
}

export const searchVideos = async (
  query: string,
  platform?: string,
  token: string
): Promise<SearchResult[]> => {
  try {
    const params = new URLSearchParams({ query });
    if (platform) {
      params.append('platform', platform);
    }
    
    const response = await fetch(
      `${API_URL}/videos/search?${params.toString()}`,
      {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      throw new Error('Search failed');
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Search error:', error);
    throw error;
  }
}; 