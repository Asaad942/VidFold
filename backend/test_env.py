from dotenv import load_dotenv
import os

# Load the environment variables
load_dotenv()

# Print the values
print("SUPABASE_URL:", os.getenv("SUPABASE_URL"))
print("SUPABASE_KEY:", os.getenv("SUPABASE_KEY"))
print("SUPABASE_JWT_SECRET:", os.getenv("SUPABASE_JWT_SECRET")) 