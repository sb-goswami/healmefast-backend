import os
import re
from app.db.vector_db import search_similar
from app.services.rag_service import embed_query
import ollama

MODEL = "llama3.2:3b"

# Fields we want to collect during triage
TRIAGE_FIELDS = [
    ("nature_of_pain", ["sharp", "dull", "burning", "aching", "throbbing", "stabbing", "cramping", "pressure", "tingling", "shooting"]),
    ("duration", ["day", "week", "month", "hour", "since", "ago", "started", "began", "long"]),
    ("severity", ["mild", "moderate", "severe", "unbearable", "slight", "bad", "worse", "better", "scale", "rate"]),
    ("location", ["left", "right", "upper", "lower", "middle", "center", "side", "front", "back", "chest", "head", "leg", "arm", "stomach", "abdomen", "neck", "shoulder", "knee", "hip", "foot", "throat"]),
    ("accompanying_symptoms", ["fever", "nausea", "vomit", "dizzy", "sweat", "cough", "breath", "fatigue", "weak", "numb", "swell", "rash", "bleed", "chills", "loss", "appetite"]),
    ("recent_event", ["fall", "injur", "accident", "exercise", "lift", "travel", "eat", "drink", "stress", "surgery", "medication"]),
]


def parse_known_facts_from_history(conversation_history: str) -> dict:
    """
    Fast Python-based parser — no LLM call needed.
    Extracts what the patient has already told us by scanning for keywords.
    """
    known = {field: "" for field, _ in TRIAGE_FIELDS}
    if not conversation_history:
        return known

    # Only look at patient lines
    patient_lines = []
    for line in conversation_history.split("\n"):
        if line.strip().lower().startswith("patient:"):
            patient_lines.append(line.lower())

    combined = " ".join(patient_lines)

    for field, keywords in TRIAGE_FIELDS:
        for kw in keywords:
            if kw in combined:
                known[field] = "mentioned"
                break

    return known


def check_symptoms(symptoms: str, conversation_history: str = "") -> str:
    """
    Fast triage — uses Python parsing (no extra LLM call) to check what's
    already known, then asks one question or gives a diagnosis.
    """
    print(f"[TOOL] check_symptoms | symptoms: {symptoms[:60]}")

    # 1. Fast Python-based fact extraction (no LLM needed)
    known = parse_known_facts_from_history(conversation_history)
    filled_count = sum(1 for v in known.values() if v)
    print(f"[TRIAGE] filled={filled_count} | known={known}")

    # 2. Get medical baseline (only if DB connected)
    try:
        query_embedding = embed_query("health conditions abnormalities risks")
        baseline_context = search_similar(query_embedding, top_k=2)
        context_str = "\n".join(baseline_context) if baseline_context else ""
    except Exception:
        context_str = ""

    baseline_section = f"\nPatient's Medical Baseline:\n{context_str}\n" if context_str else ""

    # 3. Build a tight, focused prompt
    recent_history = conversation_history.strip()[-1500:] if conversation_history else "None"

    if filled_count < 3:
        # Determine next unanswered field to ask about
        unanswered = [field for field, _ in TRIAGE_FIELDS if not known.get(field)]
        next_field = unanswered[0] if unanswered else None

        field_question_map = {
            "nature_of_pain": "How would you describe the pain or discomfort?",
            "duration": "How long have you been experiencing this?",
            "severity": "How severe is it on a scale from mild to severe?",
            "location": "Can you pinpoint the exact location?",
            "accompanying_symptoms": "Are you experiencing any other symptoms alongside this?",
            "recent_event": "Have you had any recent injury, unusual activity, or event that might be related?",
        }

        question = field_question_map.get(next_field, "Can you describe your symptoms in more detail?")

        prompt = f"""You are a medical triage AI. A patient says: "{symptoms}"
{baseline_section}
Recent conversation:
{recent_history}

Ask this ONE question to gather more information: "{question}"
Give 3-4 short answer options in EXACTLY this format (one per line):
[Option: <choice>]
[Option: Other (please describe)]

Do not add any other text. Just the question and the options."""

    else:
        # Enough info — give diagnosis
        prompt = f"""You are a medical triage AI. Based on this conversation:
{recent_history}
{baseline_section}

The patient originally reported: "{symptoms}"

Give a concise medical assessment:
**Possible Conditions:** (2-3 bullet points)
**Warning Signs to Watch:** (brief)  
**Recommended Action:** (one clear action)
*Disclaimer: I am an AI. Please consult a real doctor.*

Be brief and professional."""

    # Single LLM call
    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0.3, "num_predict": 400}
    )
    return response["message"]["content"]


# Schema for Ollama agent
check_symptoms_schema = {
    "type": "function",
    "function": {
        "name": "check_symptoms",
        "description": (
            "Triage and analyze symptoms reported by the user. Use when the user describes "
            "physical symptoms (headache, pain, fever, dizziness etc.) or answers a follow-up symptom question."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "symptoms": {
                    "type": "string",
                    "description": "User's reported symptoms or latest answer about their symptoms."
                },
                "conversation_history": {
                    "type": "string",
                    "description": "Full prior conversation for context."
                }
            },
            "required": ["symptoms"]
        }
    }
}
