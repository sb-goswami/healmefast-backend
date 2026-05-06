import os
import json
import sys
import asyncio
import re
from groq import Groq
from dotenv import load_dotenv
from app.tools.report_tool import analyze_health_report, analyze_health_report_schema
from app.tools.symptom_tool import check_symptoms, check_symptoms_schema
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

load_dotenv()
# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def serialize_message(msg):
    """Convert Groq Message object to pure dict for MongoDB storage."""
    if isinstance(msg, dict):
        return msg
    
    try:
        if hasattr(msg, 'model_dump'):
            return msg.model_dump(exclude_none=True)
        elif hasattr(msg, 'dict'):
            return msg.dict(exclude_none=True)
    except Exception:
        pass
        
    res = {
        "role": getattr(msg, "role", "assistant"),
        "content": getattr(msg, "content", "") or ""
    }
    tool_calls = getattr(msg, "tool_calls", None)
    if tool_calls:
        res["tool_calls"] = []
        for t in tool_calls:
            res["tool_calls"].append({
                "id": getattr(t, "id", ""),
                "type": "function",
                "function": {
                    "name": getattr(t.function, "name", ""),
                    "arguments": getattr(t.function, "arguments", "")
                }
            })
    return res

AVAILABLE_TOOLS = [
    analyze_health_report_schema,
    check_symptoms_schema
]

async def get_mcp_tools():
    python_exe = sys.executable
    server_path = os.path.join(os.path.dirname(__file__), "..", "..", "hospital_mcp.py")
    
    server_params = StdioServerParameters(
        command=python_exe,
        args=[server_path],
        env=os.environ.copy()
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools_result = await session.list_tools()
                
                mcp_tools = []
                for t in tools_result.tools:
                    mcp_tools.append({
                        "type": "function",
                        "function": {
                            "name": t.name,
                            "description": t.description,
                            "parameters": t.inputSchema
                        }
                    })
                return mcp_tools
    except Exception as e:
        print(f"Failed to load MCP tools: {e}")
        return []

MCP_TOOLS = []
MCP_TOOL_NAMES = []
mcp_initialized = False

async def ensure_mcp_initialized():
    global MCP_TOOLS, MCP_TOOL_NAMES, mcp_initialized
    if not mcp_initialized:
        print("[Agent] Initializing MCP tools...")
        MCP_TOOLS = await get_mcp_tools()
        for tool in MCP_TOOLS:
            if tool not in AVAILABLE_TOOLS:
                AVAILABLE_TOOLS.append(tool)
        MCP_TOOL_NAMES = [t["function"]["name"] for t in MCP_TOOLS]
        mcp_initialized = True
        print(f"[Agent] Loaded {len(MCP_TOOLS)} MCP tools.")

async def execute_mcp_tool(function_name: str, arguments: dict):
    await ensure_mcp_initialized()
    python_exe = sys.executable
    server_path = os.path.join(os.path.dirname(__file__), "..", "..", "hospital_mcp.py")
    
    server_params = StdioServerParameters(
        command=python_exe,
        args=[server_path],
        env=os.environ.copy()
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(function_name, arguments)
            if result and result.content:
                return result.content[0].text
            return "No output from tool."

SYSTEM_PROMPT = """You are an AI healthcare assistant.

YOUR ROLE:
- Help users understand their medical reports and lab results
- Extract relevant values from reports
- Explain whether values are normal, high, or low

ALLOWED:
- Analyze uploaded reports
- Explain test results in simple terms
- Highlight abnormal findings
- Give general health insights (non-prescriptive)

DOCTOR & BOOKING RULES (STRICT):
1. For mild/moderate symptoms, ONLY suggest diet, lifestyle, and exercise. Do NOT suggest a doctor.
2. ONLY if symptoms are CRITICAL or the user asks for a doctor, ask: "Would you like me to find a specialist for you?"
3. YOU MUST USE THE 'search_doctors' TOOL to find doctors. DO NOT INVENT DOCTOR NAMES.
4. Pass the exact doctor name/details to 'get_doctor_slots' to see available times.
5. Use 'book_appointment' when the user selects a slot.
6. When a tool returns `[Option: ...]`, YOU MUST REPEAT IT EXACTLY IN YOUR RESPONSE so the UI renders buttons.

NOT ALLOWED:
- Do NOT give medical diagnosis
- Do NOT prescribe medicines or treatment plans
- Do NOT replace a doctor

REFUSAL RULE:
- Only refuse if the question is completely unrelated to health
- NEVER refuse valid health-report or symptom-related questions

RESPONSE STYLE:
- Clear, short, helpful
- Mention values when available
- If values missing → say "Not found in report"
- Do NOT mention tool names
"""

async def run_agent(user_message: str, history: list = None) -> dict:
    """Main agent loop for handling user queries."""
    await ensure_mcp_initialized()
    if not user_message or user_message.strip() == "":
        user_message = "analyze my report"

    if history is None:
        history = []

    if not history or history[0].get("role") != "system":
        history.insert(0, {"role": "system", "content": SYSTEM_PROMPT})

    history.append({"role": "user", "content": user_message})

    print(f"[Agent] User: {user_message}")

    user_text = user_message.lower()

    if " at " in user_message and any(x in user_message for x in ["AM", "PM"]):
        doc_selection = "Unknown Doctor"
        if len(history) >= 3:
            doc_selection = history[-3].get("content", "Unknown Doctor")
        
        tool_result = await execute_mcp_tool("book_appointment", {
            "doctor_selection": doc_selection,
            "time_slot": user_message
        })
        
        history.append({"role": "assistant", "content": tool_result})
        return {"answer": tool_result, "tool_used": "book_appointment", "history": history}

    elif user_message.startswith("Dr. ") and " - " in user_message:
        tool_result = await execute_mcp_tool("get_doctor_slots", {"doctor_selection": user_message})
        history.append({"role": "assistant", "content": tool_result})
        return {"answer": tool_result, "tool_used": "get_doctor_slots", "history": history}

    specialties = [
        "cardiologist", "endocrinologist", "dermatologist", "orthopedic", 
        "physician", "neurologist", "pediatrician", "psychiatrist", 
        "gynecologist", "gastroenterologist", "pulmonologist", 
        "oncologist", "ophthalmologist", "ent specialist", "urologist"
    ]
    booking_intent = ["book", "find", "consult", "appointment", "search", "need", "want", "doctor", "specialist"]
    
    found_spec = next((word for word in specialties if word in user_text), None)
    has_intent = any(intent in user_text for intent in booking_intent)
    
    if has_intent and (found_spec or "doctor" in user_text or "specialist" in user_text):
        spec_to_search = found_spec if found_spec else "general physician"
        tool_result = await execute_mcp_tool("search_doctors", {"specialty": spec_to_search})
        history.append({"role": "assistant", "content": tool_result})
        return {"answer": tool_result, "tool_used": "search_doctors", "history": history}

    report_keywords = [
        "report", "test", "value", "blood", "sugar", "cholesterol",
        "kidney", "liver", "thyroid", "lipid", "level"
    ]

    if any(word in user_message.lower() for word in report_keywords):
        print("[FORCED] Using report_tool")

        tool_result = analyze_health_report(user_message)
        
        tool_result_str = f"Here is the relevant data from the health report:\n{tool_result}\n\nPlease answer the user's question based on this data."

        history.append({
            "role": "user",
            "content": f"[SYSTEM: Tool Output for analyze_health_report]\n{tool_result_str}"
        })

        final_response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=history,
            temperature=0
        )

        final_message = final_response.choices[0].message
        content = final_message.content or ""

        history.append(serialize_message(final_message))

        return {
            "answer": content,
            "tool_used": "analyze_health_report",
            "history": history
        }

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=history,
        tools=AVAILABLE_TOOLS,
        tool_choice="auto",
        temperature=0.2,
        max_tokens=200
    )

    assistant_message = response.choices[0].message
    history.append(serialize_message(assistant_message))

    tool_used = None

    if assistant_message.tool_calls:
        for tool in assistant_message.tool_calls:
            function_name = tool.function.name
            arguments = json.loads(tool.function.arguments)
            tool_used = function_name

            if function_name == "analyze_health_report":
                tool_result = analyze_health_report(**arguments)
                tool_result_str = f"Here is the relevant data from the health report:\n{tool_result}\n\nPlease answer the user's question based on this data."

                history.append({
                    "role": "tool",
                    "tool_call_id": tool.id,
                    "name": function_name,
                    "content": tool_result_str
                })

                final_response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=history,
                    temperature=0
                )

                final_message = final_response.choices[0].message
                history.append(serialize_message(final_message))

                return {
                    "answer": final_message.content or "",
                    "tool_used": tool_used,
                    "history": history
                }

            elif function_name == "check_symptoms":
                convo_lines = []
                for m in history:
                    role = m.get("role", "")
                    content = m.get("content", "")
                    if role == "user" and content:
                        convo_lines.append(f"Patient: {content}")
                    elif role == "assistant" and content:
                        convo_lines.append(f"Doctor AI: {content}")

                arguments["conversation_history"] = "\n".join(convo_lines[-30:])

                tool_result = check_symptoms(**arguments)
                
                history.append({
                    "role": "tool",
                    "tool_call_id": tool.id,
                    "name": function_name,
                    "content": "Symptom check completed. Present this exact text to the user: " + tool_result
                })
                
                history.append({
                    "role": "assistant",
                    "content": tool_result
                })

                return {
                    "answer": tool_result,
                    "tool_used": tool_used,
                    "history": history
                }

            elif function_name in MCP_TOOL_NAMES:
                tool_result = await execute_mcp_tool(function_name, arguments)
                tool_result_str = f"Result from MCP tool:\n{tool_result}\n\nPlease present this to the user."

                history.append({
                    "role": "tool",
                    "tool_call_id": tool.id,
                    "name": function_name,
                    "content": tool_result_str
                })

                final_response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=history,
                    temperature=0
                )

                final_message = final_response.choices[0].message
                history.append(serialize_message(final_message))

                return {
                    "answer": final_message.content or "",
                    "tool_used": tool_used,
                    "history": history
                }

    return {
        "answer": assistant_message.content or "",
        "tool_used": None,
        "history": history
    }