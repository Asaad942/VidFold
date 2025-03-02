"""
Database module for VidFold backend
"""
from supabase import create_client, Client
from ..core.config import settings

# Initialize Supabase client
supabase_url = settings.SUPABASE_URL.strip()
supabase_key = settings.SUPABASE_KEY.strip()

if not supabase_url or not supabase_key:
    raise ValueError("Supabase URL and key must be provided")

try:
    supabase: Client = create_client(supabase_url, supabase_key)
except Exception as e:
    raise Exception(f"Failed to initialize Supabase client: {str(e)}")

__all__ = ['supabase'] 