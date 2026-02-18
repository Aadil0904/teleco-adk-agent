import asyncio
import os
import pandas as pd
from dotenv import load_dotenv

# Import your tools and agent
from agents.orchestrator.orchestrator import orchestrator
from agents.qoe_agent.qoe_tools import IPDR_DF # We import the DF directly to scan it
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

load_dotenv()

# --- Helper Function to Scan Users ---
def get_risky_users(limit=20):
    """
    Finds top users by video usage. 
    If limit is None, returns ALL users with > 1GB usage.
    """
    print(f"🔍 Scanning entire database...")
    
    # Filter for Video
    video_traffic = IPDR_DF[IPDR_DF['app_category'].isin(['Netflix', 'YouTube'])]
    
    # Group by User
    usage = video_traffic.groupby('msisdn')['bytes_downlink'].sum()
    
    # Convert to GB
    usage_gb = usage / (1024**3)
    
    # Filter: Only show users with > 5GB usage (Real "Risk" candidates)
    risky_users = usage_gb[usage_gb > 5].sort_values(ascending=False)
    
    if limit:
        return risky_users.head(limit)
    return risky_users

# --- Interactive Chat Loop ---
async def main():
    print("="*60)
    print("🚀 TELECO SELF-HEALING DASHBOARD (Interactive Mode)")
    print("="*60)
    print("Commands:")
    print(" - 'scan':    List top 20 risky users")
    print(" - 'scan all': List EVERY risky user")
    print(" - 'analyze <phone>': Run deep diagnosis on a specific user")
    print(" - 'fix <location>': Check network status for a city")
    print(" - 'exit':    Quit")
    print("-" * 60)

    # Initialize ADK Runner once
    session_service = InMemorySessionService()
    runner = Runner(
        app_name="teleco_dashboard",
        agent=orchestrator,
        session_service=session_service
    )
    
    # Create a persistent session for the chat
    session_id = "dashboard_session"
    await session_service.create_session(app_name="teleco_dashboard", session_id=session_id, user_id="admin")

    while True:
        # 1. Get User Input
        user_input = input("\nAdmin@Teleco:~$ ").strip()
        
        if user_input.lower() == 'exit':
            print("Shutting down dashboard...")
            break
            
        # 2. Handle "Scan" command natively (Python is faster than LLM for this)
        if user_input.lower().startswith('scan'):
            limit = 20
            if 'all' in user_input.lower():
                limit = None # No limit
            
            risky = get_risky_users(limit)
            print(f"\n📋 FOUND {len(risky)} RISKY SUBSCRIBERS:")
            print(f"{'MSISDN':<15} | {'USAGE (GB)':<10}")
            print("-" * 30)
            for msisdn, gb in risky.items():
                print(f"{msisdn:<15} | {gb:.2f}")
            print("-" * 30)
            print("Tip: Type 'analyze <number>' to see the fix.")
            continue

        # 3. Handle specific "Analyze" or "Fix" queries via the Orchestrator LLM
        # We wrap the user's natural language into a prompt for the agent
        print(f"\n🤖 Agent is thinking...", end="", flush=True)
        
        user_msg = genai_types.Content(role="user", parts=[genai_types.Part(text=user_input)])
        
        async for event in runner.run_async(user_id="admin", session_id=session_id, new_message=user_msg):
            # Print text as it streams
            if getattr(event, 'content', None) and event.content.parts:
                for part in event.content.parts:
                    if getattr(part, 'text', None):
                        print(part.text, end="", flush=True)
        print("\n")

if __name__ == "__main__":
    asyncio.run(main())