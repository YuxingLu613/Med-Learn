#!/usr/bin/env python3
"""Quick test to verify DeepSeek API connection."""

import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

try:
    client = OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com"
    )

    print("Testing DeepSeek API connection...")

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'API connection successful!' if you can read this."}
        ],
        max_tokens=50
    )

    print(f"✅ Success! Response: {response.choices[0].message.content}")
    print("\nDeepSeek API is configured correctly!")

except Exception as e:
    print(f"❌ Error: {e}")
    print("\nPlease check your DEEPSEEK_API_KEY in the .env file.")
