import os
from dotenv import load_dotenv
import anthropic

load_dotenv()

print("Testing API Keys...")
print("=" * 50)

# Check environment variables
anthropic_key = os.getenv('ANTHROPIC_API_KEY')
fireflies_key = os.getenv('FIREFLIES_API_KEY')

print(f"ANTHROPIC_API_KEY: {'Found' if anthropic_key else 'Missing'}")
if anthropic_key:
    print(f"  Key starts with: {anthropic_key[:10]}...")
    print(f"  Key length: {len(anthropic_key)}")

print(f"FIREFLIES_API_KEY: {'Found' if fireflies_key else 'Missing'}")

# Test Claude client initialization
if anthropic_key:
    try:
        client = anthropic.Anthropic(api_key=anthropic_key)
        print("\nTesting Claude API...")
        
        # Try different model names
        models = ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"]
        
        for model in models:
            try:
                print(f"  Trying model: {model}")
                response = client.messages.create(
                    model=model,
                    max_tokens=100,
                    messages=[{"role": "user", "content": "Say 'test successful' if you can read this."}]
                )
                print(f"  SUCCESS with {model}: {response.content[0].text}")
                break
            except Exception as e:
                print(f"  Failed with {model}: {str(e)[:100]}")
        
        print(f"Claude Response: {response.content[0].text}")
        
    except Exception as e:
        print(f"Claude Error: {e}")