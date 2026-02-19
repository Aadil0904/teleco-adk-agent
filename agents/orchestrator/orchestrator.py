import os
from dotenv import load_dotenv
from google.adk.models.lite_llm import LiteLlm
from google.adk.agents import LlmAgent

# Import the raw data tools
from agents.qoe_agent.qoe_tools import get_comprehensive_user_context
from agents.network_agent.network_tools import check_tower_status

load_dotenv()

azure_model = LiteLlm(
    model=f"azure/{os.getenv('AZURE_OPENAI_DEPLOYMENT')}",
    api_key=os.getenv("AZURE__API_KEY"), 
    api_base=os.getenv("AZURE_API_BASE"),
    api_version=os.getenv("AZURE_API_VERSION")
)

# --- 1. MULTI-AGENT DELEGATION WRAPPERS ---

def consult_qoe_specialist(msisdn: str) -> str:
    """Delegates the analysis to the QoE & Billing Specialist Agent."""
    print(f"\n[Orchestrator] 🤝 Consulting QoE & Billing Specialist for {msisdn}...")
    raw_data = get_comprehensive_user_context(msisdn)
    
    return f"""
    [QOE SPECIALIST FINDINGS]
    Data for {msisdn}: {raw_data}
    
    Action Plan Logic:
    - If Billing Issue is "SYSTEM MISMATCH" -> Initiate urgent billing audit and refund.
    - If Billing Issue is "HIGH OVERAGES" -> Overage is correct, but high churn risk. Pitch plan upgrade.
    - If Billing Issue is "NONE" -> Confirm billing is healthy.
    - If Stream Risk is "HIGH" -> Mandate 5G Network Slicing / Priority QoS immediately to stop buffering.
    - If Voice Risk is "HIGH" -> Push VoWiFi profile update to their device.
    """

def consult_network_specialist(location: str) -> str:
    """Delegates the analysis to the Network Infrastructure Agent."""
    print(f"\n[Orchestrator] 🤝 Consulting Network Specialist for {location}...")
    raw_data = check_tower_status(location)
    
    return f"""
    [NETWORK SPECIALIST FINDINGS]
    Data for {location}: {raw_data}
    
    Diagnostic Logic Applied:
    - CRITICAL CONGESTION = Advise Dynamic Load Balancing immediately.
    - HEALTHY = Confirm infrastructure is stable.
    """

# --- 2. THE ORCHESTRATOR AGENT ---

ORCHESTRATOR_PROMPT = """
You are the **Lead NOC Executive**. 
Your team of specialists provides you with raw data and diagnostic logic. Your job is to synthesize this into a polished, personalized, and natural response.

YOUR TEAM (TOOLS):
1. `consult_qoe_specialist(msisdn)`: Gets user-specific billing, voice, and streaming analysis.
2. `consult_network_specialist(location)`: Gets cell tower congestion status.

YOUR DIRECTIVES:
1. Delegate to the correct specialist(s) to get the facts.
2. Draft a highly professional "Executive Action Plan".
3. **CRITICAL:** Do NOT mention "Specialist Rules", "Agents", "Diagnostic Logic", or internal tools in your response. 
4. Speak directly and naturally. Frame the insights as your own expert analysis.

OUTPUT FORMAT:
- **Executive Summary:** (Briefly state the user's current situation).
- **Root Cause Analysis:** (What is actually causing their friction?).
- **Actionable Resolution:** (The exact steps to fix it, e.g., plan upgrades, network slicing, audits).
"""

orchestrator = LlmAgent(
    name="Orchestrator",
    model=azure_model,
    instruction=ORCHESTRATOR_PROMPT,
    tools=[consult_qoe_specialist, consult_network_specialist] 
)