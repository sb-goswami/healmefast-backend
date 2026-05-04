import asyncio
import sys
import os

# Ensure the app module can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.agent_service import run_agent

async def main():
    print("Testing Groq Agent Integration...")
    
    print("\n--- Test 1: Symptom Checker & Doctor Suggestion ---")
    res1 = await run_agent("I have been having severe chest pain and left arm numbness since morning.")
    print(f"Tool Used: {res1.get('tool_used')}")
    with open("test_output2.json", "w", encoding="utf-8") as f:
        import json
        json.dump(res1, f, indent=2)
    print("Wrote output to test_output2.json")

if __name__ == "__main__":
    asyncio.run(main())
