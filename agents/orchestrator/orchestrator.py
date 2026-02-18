import os
from dotenv import load_dotenv
from google.adk.models.lite_llm import LiteLlm
from google.adk.agents import LlmAgent

# Import Tools
from agents.qoe_agent.qoe_tools import analyze_streaming_usage
from agents.network_agent.network_tools import check_tower_status

load_dotenv()

# Configure Azure
azure_model = LiteLlm(
    model=f"azure/{os.getenv('AZURE_OPENAI_DEPLOYMENT')}",
    api_key=os.getenv("AZURE__API_KEY"), 
    api_base=os.getenv("AZURE_API_BASE"),
    api_version=os.getenv("AZURE_API_VERSION")
)

# --- NEW INTELLIGENT PROMPT ---
# ... (imports are same)

PROMPT = """
You are the **AI Customer Experience Lead** for a Telecom. 
Your goal is to propose **Hyper-Personalized** solutions. 

**YOUR DATA:**
- `analyze_streaming_usage(msisdn)`: Tells you *Who* they are (Device, Habits, Favorite App).
- `check_tower_status(location)`: Tells you *Where* they are (Congestion).

**INSTRUCTIONS:**
1. **Analyze the Persona:** - If they use an **iPhone 15** and watch **Netflix**, they value Quality -> Pitch "4K Streaming Pass".
   - If they are a **"Late Night Binger"**, pitch a "Midnight Owl Bundle" (Data free after 11 PM).
   - If they are a **"Commuter"**, pitch a "Stable Connection Guarantee" for transit routes.

2. **Check the Stats:**
   - Only suggest Data Top-ups if they are actually running low (>90% used).
   - Otherwise, focus on **Speed/Priority** upgrades.

**OUTPUT FORMAT:**
- **User Vibe:** (e.g., "High-value iPhone user who loves late-night Netflix")
- **The Problem:** (e.g., "Buffering during their favorite show")
- **The "Hyper-Personal" Fix:** (Invent a catchy name for the plan/bundle based on their specific habit).
"""

orchestrator = LlmAgent(
    name="Orchestrator",
    model=azure_model,
    instruction=PROMPT,
    tools=[analyze_streaming_usage, check_tower_status]
)