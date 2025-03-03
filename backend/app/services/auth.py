import logging
from supabase import create_client, Client
from typing import Optional, Dict, Any
from ..core.config import settings

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self):
        try:
            # Log the Supabase package version
            import supabase
            logger.debug(f"Supabase package version: {supabase.__version__}")
            
            # Remove any trailing spaces from the URL and key
            supabase_url = settings.SUPABASE_URL.strip()
            supabase_key = settings.SUPABASE_KEY.strip()
            
            # Log the URL and key (masked for security)
            logger.debug(f"Supabase URL: {supabase_url}")
            logger.debug(f"Supabase key length: {len(supabase_key)}")
            
            if not supabase_url or not supabase_key:
                raise ValueError("Supabase URL and key must be provided")
            
            # Log that we're about to create the client
            logger.debug("Attempting to create Supabase client...")
            
            try:
                # Initialize Supabase client with minimal configuration
                self.supabase: Client = create_client(
                    supabase_url=supabase_url,
                    supabase_key=supabase_key,
                    options={
                        "auth": {
                            "autoRefreshToken": True,
                            "persistSession": True,
                            "detectSessionInUrl": False
                        }
                    }
                )
                logger.debug("Supabase client created successfully")
            except TypeError as type_error:
                logger.error(f"TypeError during client creation: {str(type_error)}")
                raise
            except ValueError as value_error:
                logger.error(f"ValueError during client creation: {str(value_error)}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error during client creation: {str(e)}")
                raise
                
        except Exception as e:
            error_msg = f"Failed to initialize Supabase client: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    async def sign_up(self, email: str, password: str) -> Dict[str, Any]:
        try:
            response = await self.supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "email_redirect_to": f"{settings.SUPABASE_URL}/auth/callback"
                }
            })
            return response.model_dump()
        except Exception as e:
            raise Exception(f"Error during sign up: {str(e)}")
    
    async def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        try:
            response = await self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            return response.model_dump()
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
            if not response or not response.user:
                return None
            return {
                "user": response.user.model_dump(),
                "access_token": access_token
            }
        except Exception as e:
            logger.error(f"Error getting user: {str(e)}")
            return None
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        try:
            response = await self.supabase.auth.refresh_session(refresh_token)
            return response.model_dump()
        except Exception as e:
            raise Exception(f"Error refreshing token: {str(e)}")

# Initialize the auth service
logger.debug("About to initialize AuthService...")
try:
    auth_service = AuthService()
    logger.debug("AuthService initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize AuthService: {str(e)}")
    raise 