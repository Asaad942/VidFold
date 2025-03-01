from openai import OpenAI
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def test_openai():
    try:
        # Initialize OpenAI client with API key from environment
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        print("Testing OpenAI API connection...")
        
        # Try to create a simple chat completion
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Using a known working model
            messages=[
                {"role": "user", "content": "write a haiku about ai"}
            ]
        )
        
        print("\nAPI test successful!")
        print("Response:", completion.choices[0].message.content)
        return True
        
    except Exception as e:
        print("\nError testing OpenAI API:")
        print(str(e))
        return False

if __name__ == "__main__":
    success = test_openai()
    if not success:
        exit(1) 