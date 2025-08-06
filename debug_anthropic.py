import traceback
import os
from dotenv import load_dotenv

load_dotenv()

try:
    import anthropic
    print(f"Anthropic version: {anthropic.__version__}")
    
    api_key = os.getenv('ANTHROPIC_API_KEY')
    print(f"API key exists: {bool(api_key)}")
    
    print("\nTrying to create client...")
    client = anthropic.Anthropic(api_key=api_key)
    print("Success!")
    
except Exception as e:
    print(f"Error: {e}")
    print("\nFull traceback:")
    traceback.print_exc()