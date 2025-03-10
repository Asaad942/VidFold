import { supabase } from '../config/supabase';

const API_URL = 'https://vidfold-backend.onrender.com/api/v1'; // Render deployment URL

export const videoService = {
  // Get all videos for the current user
  getUserVideos: async () => {
    try {
      console.log('Getting user from auth...');
      const { data: { user }, error: authError } = await supabase.auth.getUser();
      
      if (authError) {
        console.error('Auth error:', authError);
        throw new Error('Authentication failed');
      }
      
      if (!user) {
        console.log('No authenticated user found');
        throw new Error('User not authenticated');
      }

      console.log('Authenticated user ID:', user.id);

      const { data, error } = await supabase
        .from('videos')
        .select(`
          *,
          video_analysis (
            search_summary,
            visual_summary,
            audio_transcription,
            keywords,
            confidence_scores,
            processing_status,
            metadata
          ),
          video_categories (
            categories (
              id,
              name
            )
          )
        `)
        .eq('user_id', user.id)
        .order('created_at', { ascending: false });

      if (error) {
        console.error('Database error:', error);
        throw error;
      }

      console.log('Videos fetched:', data ? data.length : 0);
      return data || [];
    } catch (error) {
      console.error('Error in getUserVideos:', error);
      throw error;
    }
  },

  // Add a new video
  addVideo: async (videoUrl, platform, title = null) => {
    try {
      // Check if user is authenticated
      const { data: { user }, error: authError } = await supabase.auth.getUser();
      
      if (authError) {
        console.error('Authentication error:', authError.message);
        throw new Error('Authentication failed');
      }
      
      if (!user) {
        throw new Error('No authenticated user found');
      }

      console.log('Attempting to add video with user_id:', user.id);

      // Insert the video into Supabase with initial status
      const { data, error: insertError } = await supabase
        .from('videos')
        .insert([
          {
            user_id: user.id,
            url: videoUrl,
            platform,
            title,
            status: 'pending',
            error: null,
            analysis: null,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
          },
        ])
        .select();

      if (insertError) {
        console.error('Insert error:', insertError);
        throw new Error(insertError.message);
      }

      if (!data || data.length === 0) {
        throw new Error('No data returned after insertion');
      }

      // Trigger video processing in the backend
      try {
        const { session } = await supabase.auth.getSession();
        const response = await fetch(`${API_URL}/videos/process`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${session?.access_token}`
          },
          body: JSON.stringify({
            video_id: data[0].id,
            url: videoUrl,
            platform: platform.toLowerCase()
          })
        });

        if (!response.ok) {
          console.warn('Video processing request failed:', await response.text());
          return { ...data[0], status: 'error' };
        }

        // Get the metadata from the response
        const processingData = await response.json();
        return { ...data[0], ...processingData.metadata };
      } catch (processingError) {
        console.warn('Error triggering video processing:', processingError);
        return { ...data[0], status: 'error' };
      }
    } catch (error) {
      console.error('Error in addVideo:', error);
      throw new Error(`Failed to add video: ${error.message}`);
    }
  },

  // Delete a video
  deleteVideo: async (videoId) => {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error('User not authenticated');

      const { error } = await supabase
        .from('videos')
        .delete()
        .eq('id', videoId)
        .eq('user_id', user.id); // Ensure user can only delete their own videos

      if (error) throw error;
      return true;
    } catch (error) {
      console.error('Error deleting video:', error.message);
      throw error;
    }
  },

  // Search videos with improved search
  searchVideos: async (query) => {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error('User not authenticated');

      const { data, error } = await supabase
        .from('videos')
        .select(`
          *,
          video_analysis!inner (
            search_summary,
            visual_summary,
            audio_transcription,
            keywords,
            confidence_scores,
            processing_status
          )
        `)
        .eq('user_id', user.id)
        .textSearch('video_analysis.search_summary', query, {
          config: 'english'
        })
        .order('created_at', { ascending: false });

      if (error) throw error;
      return data || [];
    } catch (error) {
      console.error('Error searching videos:', error);
      throw error;
    }
  },

  // Add video to category
  addToCategory: async (videoId, categoryId) => {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error('User not authenticated');

      const { error } = await supabase
        .from('video_categories')
        .insert([
          {
            video_id: videoId,
            category_id: categoryId,
          },
        ]);

      if (error) throw error;
      return true;
    } catch (error) {
      console.error('Error adding video to category:', error.message);
      throw error;
    }
  },

  // Check video processing status with detailed info
  checkProcessingStatus: async (videoId) => {
    try {
      const { data, error } = await supabase
        .from('videos')
        .select(`
          *,
          video_analysis (
            visual_summary,
            audio_transcription,
            keywords,
            confidence_scores,
            processing_status,
            metadata
          )
        `)
        .eq('id', videoId)
        .single();

      if (error) throw error;
      return data;
    } catch (error) {
      console.error('Error checking video status:', error);
      throw error;
    }
  },

  // Remove video from category
  removeFromCategory: async (videoId, categoryId) => {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error('User not authenticated');

      const { error } = await supabase
        .from('video_categories')
        .delete()
        .match({ video_id: videoId, category_id: categoryId });

      if (error) throw error;
      return true;
    } catch (error) {
      console.error('Error removing video from category:', error);
      throw error;
    }
  }
}; 