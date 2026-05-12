import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_answer(context, question):
    prompt = f"""
You are a strict medical assistant.

RULES (MANDATORY):
- ONLY use values explicitly present in Context
- NEVER create or assume values
- NEVER change numbers
- If value not present → say "Not found in report"
- DO NOT give medical advice or disease prediction

TASK:
- Extract relevant values
- State if they are normal or not (only if obvious)
- If unsure → say "Cannot determine"

Context:
{context}

Question:
{question}

Answer:
- Short
- Exact
- No assumptions
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    return response.choices[0].message.content.strip()

def generate_initial_analysis(report_text):
    if not report_text or "No text extracted" in report_text or len(report_text) < 50:
        return "I couldn't read the report clearly. Please upload a higher-quality photo or PDF so I can provide an accurate analysis."

    prompt = f"""You are an expert medical AI assistant. The user just uploaded their health report.
Scan the report and provide an initial analysis.

STRICT RULES:
1. ONLY focus on values that are explicitly outside the "Reference Range" or "Interval" mentioned in the report.
2. If a value is within the normal range, DO NOT list it as abnormal.
3. If no reference range is found for a specific test, do NOT guess. Say "Cannot determine (range missing)".
4. NEVER invent or assume values. Only use what is in the text.
5. If everything is normal, say "Your report looks completely normal! Keep up the healthy lifestyle."
6. Focus on one finding per bullet point.

TEMPLATE:
### ⚠️ Abnormal Findings
* **[Finding Name]**: [Value] (Range: [Range]). [Brief reason why it's abnormal]. Actionable lifestyle or diet suggestion: [suggestion].

### 🚨 Critical Findings
* **[Finding Name]**: [Value] (Range: [Range]). [Potential risk]. 👨‍⚕️ **Action required:** Consult [Specialist] immediately.
* If none: "None found."

Report Text:
{report_text}"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=600
    )
    return response.choices[0].message.content