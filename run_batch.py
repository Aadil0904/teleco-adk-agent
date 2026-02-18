import asyncio
import os
import pandas as pd
from dotenv import load_dotenv

# Import the Agent and the Scanner Tool
from agents.orchestrator.orchestrator import orchestrator
from agents.qoe_agent.qoe_tools import scan_for_risky_users
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

load_dotenv()

async def analyze_user(runner, msisdn, session_id):
    """
    Runs the Orchestrator for a SINGLE user to get a personalization plan.
    """
    # We construct a specific prompt for this user
    query = f"Analyze user {msisdn}. They are flagged for high usage. Check their profile and usage, then propose a 'Personalized Bundle' or 'Network Fix'."
    
    print(f"\n⚡ Processing User: {msisdn}...")
    
    user_msg = genai_types.Content(role="user", parts=[genai_types.Part(text=query)])
    
    final_recommendation = ""
    
    # Run the agent
    async for event in runner.run_async(user_id="admin", session_id=session_id, new_message=user_msg):
        # Capture the final text response
        if getattr(event, 'content', None) and event.content.parts:
            for part in event.content.parts:
                if getattr(part, 'text', None):
                    final_recommendation += part.text

    return final_recommendation

async def main():
    print("🚀 Starting Proactive Risk Scanner...")
    
    # 1. Setup ADK Runner
    session_service = InMemorySessionService()
    runner = Runner(
        app_name="teleco_batch",
        agent=orchestrator,
        session_service=session_service
    )

    # 2. SCAN: Find the High Risk Users (Python Logic)
    risky_msisdns = scan_for_risky_users(limit=3) # Let's do top 3 for the demo
    
    print(f"📋 Found {len(risky_msisdns)} candidates: {risky_msisdns}")
    
    # 3. LOOP: Process each user
    results = []
    
    for i, msisdn in enumerate(risky_msisdns):
        # Create a unique session for each user analysis
        session_id = f"session_batch_{i}"
        await session_service.create_session(app_name="teleco_batch", session_id=session_id, user_id="admin")
        
        # Get the LLM's fix
        recommendation = await analyze_user(runner, msisdn, session_id)
        
        # Save structured result
        results.append({
            "MSISDN": msisdn,
            "Status": "High Risk",
            "Proposed_Fix": recommendation
        })
    
    # 4. FINAL REPORT
    print("\n" + "="*50)
    print("📢 FINAL PERSONALIZATION REPORT")
    print("="*50)
    
    for res in results:
        print(f"\n👤 USER: {res['MSISDN']}")
        print(f"⚠️ STATUS: {res['Status']}")
        print(f"🛠 FIX: {res['Proposed_Fix'].strip()}")
        print("-" * 30)
    
    # Optional: Save to CSV for your manager
    # pd.DataFrame(results).to_csv("final_report.csv", index=False)
    # print("\n✅ Report saved to final_report.csv")

if __name__ == "__main__":
    asyncio.run(main())