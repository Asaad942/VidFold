import asyncio
from app.services.auth import auth_service

async def test_connection():
    try:
        # Try to get user with an invalid token to test connection
        result = await auth_service.get_user("invalid_token")
        print("✅ Successfully connected to Supabase!")
        print("Note: Expected None for result with invalid token:", result is None)
    except Exception as e:
        print("❌ Error connecting to Supabase:")
        print(str(e))

if __name__ == "__main__":
    asyncio.run(test_connection()) 