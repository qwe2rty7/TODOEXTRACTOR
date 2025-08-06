import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

print("Testing Anthropic client initialization...")
api_key = os.getenv('ANTHROPIC_API_KEY')
print(f"API Key present: {bool(api_key)}")

try:
    # Try basic initialization
    print("\nAttempt 1: Basic initialization with api_key parameter")
    client = anthropic.Anthropic(api_key=api_key)
    print("Success!")
except Exception as e:
    print(f"Failed: {e}")

try:
    # Try without any parameters
    print("\nAttempt 2: Initialization without parameters (uses env var)")
    os.environ['ANTHROPIC_API_KEY'] = api_key
    client = anthropic.Anthropic()
    print("Success!")
except Exception as e:
    print(f"Failed: {e}")

print("\nChecking anthropic version:")
print(f"Version: {anthropic.__version__}")