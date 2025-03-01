from supabase import create_client
from .config import get_settings

settings = get_settings()

supabase = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_KEY
) 