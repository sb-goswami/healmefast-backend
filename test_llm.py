import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.llm_service import generate_initial_analysis

def main():
    print("Testing Groq LLM Service directly...")
    
    report_text = """
    Patient: John Doe
    Age: 45
    Blood Sugar: 250 mg/dL (High)
    Cholesterol: 180 mg/dL (Normal)
    """
    
    print("\n--- Initial Analysis ---")
    res = generate_initial_analysis(report_text)
    with open("test_output.txt", "w", encoding="utf-8") as f:
        f.write(res)
    print("Wrote output to test_output.txt")

if __name__ == "__main__":
    main()
