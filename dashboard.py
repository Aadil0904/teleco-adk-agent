import asyncio
import os
from dotenv import load_dotenv

from agents.orchestrator.orchestrator import orchestrator
from agents.qoe_agent.qoe_tools import scan_all_risks
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

load_dotenv()

async def main():
    print("="*80)
    print("🚀 TELECO AI NOC - MULTI-DIMENSIONAL RISK DASHBOARD")
    print("="*80)
    print("Commands:")
    print(" - 'scan':    List top 20 users across all risk pillars")
    print(" - 'analyze <phone>': Run deep AI diagnosis on a specific user")
    print(" - 'exit':    Quit")
    print("-" * 80)

    session_service = InMemorySessionService()
    runner = Runner(
        app_name="teleco_dashboard",
        agent=orchestrator,
        session_service=session_service
    )
    
    session_id = "dashboard_session"
    await session_service.create_session(app_name="teleco_dashboard", session_id=session_id, user_id="admin")

    while True:
        user_input = input("\nAdmin@NOC:~$ ").strip()
        
        if user_input.lower() == 'exit':
            break
            
        if user_input.lower().startswith('scan'):
            limit = 20 if 'all' not in user_input.lower() else 500
            risky = scan_all_risks(limit)
            
            print(f"\n📋 FOUND {len(risky)} HIGH-PRIORITY SUBSCRIBERS:")
            # Multi-column UI Printout
            print(f"{'MSISDN':<15} | {'VOICE RISK':<12} | {'STREAM RISK':<12} | {'QUOTA RISK':<15} | {'BILLING MISMATCH'}")
            print("-" * 75)
            for row in risky:
                print(f"{row['MSISDN']:<15} | {row['Voice']:<12} | {row['Stream']:<12} | {row['Quota']:<15} | {row['Billing']}")
            print("-" * 75)
            continue

        print(f"\n🤖 Connecting to Multi-Agent System...", end="", flush=True)
        user_msg = genai_types.Content(role="user", parts=[genai_types.Part(text=user_input)])
        
        async for event in runner.run_async(user_id="admin", session_id=session_id, new_message=user_msg):
            if getattr(event, 'content', None) and event.content.parts:
                for part in event.content.parts:
                    if getattr(part, 'text', None):
                        print(part.text, end="", flush=True)
        print("\n")

if __name__ == "__main__":
    asyncio.run(main())