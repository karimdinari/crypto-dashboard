import os
from dotenv import load_dotenv

load_dotenv()

print(f"EXCHANGERATE_API_KEY: '{os.getenv('EXCHANGERATE_API_KEY', 'NOT SET')}'")
print(f"Key length: {len(os.getenv('EXCHANGERATE_API_KEY', ''))}")

if os.getenv('EXCHANGERATE_API_KEY'):
    print("✅ API key is loaded!")
else:
    print("❌ API key is NOT loaded")