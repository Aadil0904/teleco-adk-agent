import os
from dotenv import load_dotenv
from google.adk.models.lite_llm import LiteLlm
from google.adk.agents import LlmAgent
from agents.network_agent.network_tools import check_tower_status

load_dotenv()

azure_model = LiteLlm(
    model=f"azure/{os.getenv('AZURE_OPENAI_DEPLOYMENT')}",
    api_key=os.getenv("AZURE__API_KEY"), 
    api_base=os.getenv("AZURE_API_BASE"),
    api_version=os.getenv("AZURE_API_VERSION")
)

NETWORK_PROMPT = """
You are the **Network Infrastructure Agent**.
Your job is to analyze cell tower congestion levels for specific locations.

CRITICAL EXPERTISE RULES:
1. If you see "CRITICAL CONGESTION", immediately recommend Dynamic Load Balancing to a backup frequency.
2. If the tower is "HEALTHY", confirm that the network infrastructure is operating normally and is not the cause of any user issues.
"""

network_agent = LlmAgent(
    name="Network_Agent",
    model=azure_model,
    instruction=NETWORK_PROMPT,
    tools=[check_tower_status]
)