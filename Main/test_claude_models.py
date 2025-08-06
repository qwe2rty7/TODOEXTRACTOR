import os
from dotenv import load_dotenv
import anthropic

load_dotenv()

print("Testing Claude API with different model names...")
print("=" * 50)

api_key = os.getenv('ANTHROPIC_API_KEY')
print(f"API Key found: {'Yes' if api_key else 'No'}")

if api_key:
    client = anthropic.Anthropic(api_key=api_key)
    
    # List of model names to try
    models_to_test = [
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229", 
        "claude-3-haiku-20240307",
        "claude-3-5-sonnet-20241022",
        "claude-3-5-sonnet-20240620",
        "claude-3-5-haiku-20241022",
        "claude-2.1",
        "claude-2.0",
        "claude-instant-1.2"
    ]
    
    print("\nTesting each model:")
    print("-" * 30)
    
    for model in models_to_test:
        try:
            print(f"Testing: {model}")
            response = client.messages.create(
                model=model,
                max_tokens=50,
                messages=[{"role": "user", "content": "Reply with 'success' only"}]
            )
            print(f"  SUCCESS: {response.content[0].text.strip()}")
            print(f"  This model works! Use: {model}")
            break
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg:
                print(f"  X Authentication error - API key is invalid")
            elif "404" in error_msg or "does not exist" in error_msg.lower():
                print(f"  X Model not found")
            elif "deprecated" in error_msg.lower():
                print(f"  X Model deprecated")
            else:
                print(f"  X Error: {error_msg[:60]}")
else:
    print("No API key found in .env file")