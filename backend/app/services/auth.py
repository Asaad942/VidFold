from supabase import create_client, Client
from typing import Optional, Dict, Any
from ..core.config import settings

class AuthService:
    def __init__(self):
        # Remove any trailing spaces from the URL and key
        supabase_url = settings.SUPABASE_URL.strip()
        supabase_key = settings.SUPABASE_KEY.strip()
        
        if not supabase_url or not supabase_key:
            raise ValueError("Supabase URL and key must be provided")
            
        try:
            # Initialize Supabase client with only required parameters
            self.supabase: Client = create_client(
                supabase_url=supabase_url,
                supabase_key=supabase_key,
                options={
                    "auto_refresh_token": True,
                    "persist_session": True
                }
            )
        except Exception as e:
            raise Exception(f"Failed to initialize Supabase client: {str(e)}")
    
    async def sign_up(self, email: str, password: str) -> Dict[str, Any]:
        try:
            response = await self.supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            return response.dict()
        except Exception as e:
            raise Exception(f"Error during sign up: {str(e)}")
    
    async def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        try:
            response = await self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            return response.dict()
        except Exception as e:
            raise Exception(f"Error during sign in: {str(e)}")
    
    async def sign_out(self, access_token: str) -> bool:
        try:
            await self.supabase.auth.sign_out()
            return True
        except Exception as e:
            raise Exception(f"Error during sign out: {str(e)}")
    
    async def get_user(self, access_token: str) -> Optional[Dict[str, Any]]:
        try:
            response = await self.supabase.auth.get_user(access_token)
            return response.dict() if response else None
        except Exception:
            return None
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        try:
            response = await self.supabase.auth.refresh_session(refresh_token)
            return response.dict()
        except Exception as e:
            raise Exception(f"Error refreshing token: {str(e)}")

# Initialize the auth service
auth_service = AuthService() 