-- Enable the necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Drop existing tables if they exist (to recreate with correct foreign keys)
DROP TABLE IF EXISTS video_categories CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS video_analysis CASCADE;
DROP TABLE IF EXISTS videos CASCADE;

-- Create the videos table if it doesn't exist
CREATE TABLE videos (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  url TEXT NOT NULL,
  platform TEXT NOT NULL,
  title TEXT,
  thumbnail_url TEXT,
  duration INTEGER,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create the video_analysis table
CREATE TABLE video_analysis (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  video_id UUID REFERENCES videos(id) ON DELETE CASCADE,
  search_summary TEXT,
  visual_summary TEXT,
  audio_transcription TEXT,
  keywords TEXT[],
  metadata JSONB,
  embedding vector(1536),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create the categories table
CREATE TABLE categories (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create the video_categories table
CREATE TABLE video_categories (
  video_id UUID REFERENCES videos(id) ON DELETE CASCADE,
  category_id UUID REFERENCES categories(id) ON DELETE CASCADE,
  PRIMARY KEY (video_id, category_id)
);

-- Create indexes for better performance
CREATE INDEX idx_videos_user_id ON videos(user_id);
CREATE INDEX idx_video_analysis_video_id ON video_analysis(video_id);
CREATE INDEX idx_categories_user_id ON categories(user_id);
CREATE INDEX idx_embedding ON video_analysis USING ivfflat (embedding vector_cosine_ops);

-- Create default categories
INSERT INTO categories (name, user_id)
SELECT name, NULL
FROM (
  VALUES 
    ('YouTube'),
    ('Instagram'),
    ('Facebook'),
    ('TikTok'),
    ('Twitter')
) AS default_categories(name)
WHERE NOT EXISTS (
  SELECT 1 FROM categories WHERE user_id IS NULL
);

-- Enable RLS (Row Level Security)
ALTER TABLE videos ENABLE ROW LEVEL SECURITY;
ALTER TABLE video_analysis ENABLE ROW LEVEL SECURITY;
ALTER TABLE categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE video_categories ENABLE ROW LEVEL SECURITY;

-- Drop existing policies
DROP POLICY IF EXISTS "Users can view own videos" ON videos;
DROP POLICY IF EXISTS "Users can insert own videos" ON videos;
DROP POLICY IF EXISTS "Users can update own videos" ON videos;
DROP POLICY IF EXISTS "Users can delete own videos" ON videos;
DROP POLICY IF EXISTS "Users can view own video analysis" ON video_analysis;
DROP POLICY IF EXISTS "Users can view own categories" ON categories;
DROP POLICY IF EXISTS "Users can insert own categories" ON categories;
DROP POLICY IF EXISTS "Users can view own video categories" ON video_categories;
DROP POLICY IF EXISTS "Users can manage own video categories" ON video_categories;

-- Create policies for videos
CREATE POLICY "Users can view own videos"
  ON videos FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own videos"
  ON videos FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own videos"
  ON videos FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own videos"
  ON videos FOR DELETE
  USING (auth.uid() = user_id);

-- Create policies for video_analysis
CREATE POLICY "Users can view own video analysis"
  ON video_analysis FOR SELECT
  USING (EXISTS (
    SELECT 1 FROM videos
    WHERE videos.id = video_analysis.video_id
    AND videos.user_id = auth.uid()
  ));

-- Create policies for categories
CREATE POLICY "Users can view own categories"
  ON categories FOR SELECT
  USING (user_id IS NULL OR auth.uid() = user_id);

CREATE POLICY "Users can insert own categories"
  ON categories FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Create policies for video_categories
CREATE POLICY "Users can view own video categories"
  ON video_categories FOR SELECT
  USING (EXISTS (
    SELECT 1 FROM videos
    WHERE videos.id = video_categories.video_id
    AND videos.user_id = auth.uid()
  ));

CREATE POLICY "Users can manage own video categories"
  ON video_categories FOR ALL
  USING (EXISTS (
    SELECT 1 FROM videos
    WHERE videos.id = video_categories.video_id
    AND videos.user_id = auth.uid()
  )); 