-- Add deleted_at column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'videos' 
        AND column_name = 'deleted_at'
    ) THEN
        ALTER TABLE videos ADD COLUMN deleted_at TIMESTAMP WITH TIME ZONE;
        CREATE INDEX idx_videos_deleted_at ON videos(deleted_at);
    END IF;
END $$; 