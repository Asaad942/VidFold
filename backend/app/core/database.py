from supabase import create_client
from .config import get_settings

settings = get_settings()

# Use service role key for backend operations
supabase = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_SERVICE_KEY  # Use service role key instead of anonymous key
) 