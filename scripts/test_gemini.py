import sys
sys.path.insert(0, '.')
import asyncio
from services.storage_service import load_llm_settings
from services.llm_service import call_gemini_api

async def main():
    s = load_llm_settings()
    print("Testing gemini-2.0-flash...")
    try:
        r2 = await call_gemini_api(
            api_key=s.api_key,
            model_name="gemini-2.0-flash",
            system_prompt="Test",
            user_prompt="Say hi"
        )
        print("gemini-2.0-flash succeeded:", r2[:50])
    except Exception as e:
        print("gemini-2.0-flash FAILED:", e)

    print("\nTesting gemini-3.5-flash...")
    try:
        r3 = await call_gemini_api(
            api_key=s.api_key,
            model_name="gemini-3.5-flash",
            system_prompt="Test",
            user_prompt="Say hi"
        )
        print("gemini-3.5-flash SUCCEEDED:", r3[:80])
    except Exception as e:
        print("gemini-3.5-flash FAILED:", e)

if __name__ == '__main__':
    asyncio.run(main())
