#!/usr/bin/env python3
"""Test Gemma 4 integration with a single lead draft generation."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.config import load_environment, get_gemini_api_key, get_gemini_model
from services.llm import generate_draft, LLMServiceError

# Test lead
TEST_LEAD = {
    "id": "test-001",
    "name": "The Riverside Café",
    "email": "info@riversidecafe.za",
    "lead_score": 85,
    "issues": "Website not mobile friendly, TTFB 3.2s",
    "advice": "Venue accepts reservations but website has no online booking. Could benefit from ad spend tracking.",
    "tags": "Restaurants, Waterfront, Scenic",
    "vibes": "Upscale, Family Friendly",
    "website": "http://riversidecafe.za",
    "address": "123 River Road, Stellenbosch",
}


def main():
    load_environment()
    
    api_key = get_gemini_api_key()
    model = get_gemini_model()
    
    print("=" * 60)
    print("MASA Gemma 4 Integration Test")
    print("=" * 60)
    print(f"Model: {model}")
    print(f"API Key: {'✅ Configured' if api_key else '❌ Missing'}")
    print(f"Test Lead: {TEST_LEAD['name']}")
    print("-" * 60)
    
    if not api_key:
        print("\n❌ GEMINI_API_KEY not found in environment.")
        print("Add it to: C:\\Users\\markussass\\Desktop\\.env.txt")
        print("Get key from: https://aistudio.google.com/apikey")
        return 1
    
    try:
        print("\n📝 Generating draft with Gemma 4...")
        result = generate_draft(TEST_LEAD)
        
        print("\n✅ SUCCESS! Draft generated:")
        print("-" * 60)
        print(f"Model Used: {result.model}")
        print(f"Subject: {result.subject}")
        print(f"\nBody ({len(result.body.split())} words):")
        print(result.body)
        print("-" * 60)
        
        # Validation checks
        word_count = len(result.body.split())
        print(f"\n✅ Word count: {word_count}/100")
        print(f"✅ Has CTA: {'Mind if I send' in result.body}")
        print(f"✅ Has opt-out: {'Opt out:' in result.body}")
        print(f"✅ Starts with Hi: {result.body.startswith('Hi ')}")
        
        if "gemini" in result.model.lower() or "gemma" in result.model.lower():
            print("\n🎉 Gemma 4 is working correctly!")
        else:
            print(f"\n⚠️  Used fallback model: {result.model}")
        
        return 0
        
    except LLMServiceError as exc:
        print(f"\n❌ LLM Error: {exc}")
        return 1
    except Exception as exc:
        print(f"\n❌ Unexpected Error: {exc}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
