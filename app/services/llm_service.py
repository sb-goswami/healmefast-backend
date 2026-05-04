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
    prompt = f"""You are an expert medical AI assistant. The user just uploaded their health report.
Scan the report and provide an initial analysis.

RULES:
- Only focus on what is important (abnormal or critical values).
- If everything is normal, say "Your report looks completely normal! Keep up the healthy lifestyle."
- Otherwise, use EXACTLY this markdown template:

### ⚠️ Abnormal Findings
* **[Finding Name]**: [Brief value/issue]. Actionable lifestyle or diet suggestion: [suggestion].

### 🚨 Critical Findings
* **[Finding Name]**: [Brief value/issue]. [Potential disease risk]. 👨‍⚕️ **Action required:** Consult [Specialist] immediately.
* If none: "None found."

Report Text:
{report_text}"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_completion_tokens=600
    )
    return response.choices[0].message.content