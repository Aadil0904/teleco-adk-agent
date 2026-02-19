import os
from dotenv import load_dotenv
from google.adk.models.lite_llm import LiteLlm
from google.adk.agents import LlmAgent
from agents.qoe_agent.qoe_tools import get_comprehensive_user_context

load_dotenv()

azure_model = LiteLlm(
    model=f"azure/{os.getenv('AZURE_OPENAI_DEPLOYMENT')}",
    api_key=os.getenv("AZURE__API_KEY"), 
    api_base=os.getenv("AZURE_API_BASE"),
    api_version=os.getenv("AZURE_API_VERSION")
)

QOE_PROMPT = """
You are the **QoE & Billing Specialist Agent**.
Your sole job is to analyze the raw telemetry for a specific subscriber and identify their exact problem.

CRITICAL EXPERTISE RULES:
1. **Billing:** If the user is on a "Basic" plan, multiple charges are normal Pay-As-You-Go data overages. Do NOT call this a billing error; suggest a plan upgrade. If the user is "Premium", extra charges ARE a billing error; flag for audit.
2. **Voice:** Voice Drops < 15s mean bad physical coverage. Suggest VoWiFi (Wi-Fi calling).
3. **Data:** Heavy video streaming requires network priority slicing.

Analyze the user and return a concise, accurate diagnosis based ONLY on these rules.
"""

qoe_agent = LlmAgent(
    name="QoE_Agent",
    model=azure_model,
    instruction=QOE_PROMPT,
    tools=[get_comprehensive_user_context]
)