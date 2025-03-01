from supabase import create_client
from dotenv import load_dotenv
import os
import asyncio

async def test_supabase():
    # Load environment variables
    load_dotenv()
    
    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL").strip()
    supabase_key = os.getenv("SUPABASE_KEY").strip()
    
    print("Testing Supabase connection...")
    print(f"URL: {supabase_url}")
    print(f"Key starts with: {supabase_key[:10]}...")
    
    try:
        # Initialize Supabase client
        supabase = create_client(
            supabase_url=supabase_url,
            supabase_key=supabase_key
        )
        print("✅ Successfully created Supabase client!")
        
        # Try a simple query
        response = await supabase.auth.get_user("invalid_token")
        print("✅ Successfully made API call (expected None response):", response is None)
        
    except Exception as e:
        print("❌ Error:", str(e))

if __name__ == "__main__":
    asyncio.run(test_supabase()) 