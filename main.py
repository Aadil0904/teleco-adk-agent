import asyncio
import os
from dotenv import load_dotenv

# Import the agent
from agents.orchestrator.orchestrator import orchestrator
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

# Load env to ensure keys are available
load_dotenv()

async def main():
    print("🚀 Teleco Orchestrator System Starting...")
    
    # 1. Initialize the Session Service
    session_service = InMemorySessionService()

    # 2. Initialize the Runner
    runner = Runner(
        app_name="teleco_demo",
        agent=orchestrator,
        session_service=session_service
    )

    # 3. FIX: Create the Session explicitly with user_id!
    session_id = "session_001"
    # Added user_id="admin" here
    await session_service.create_session(
        app_name="teleco_demo", 
        session_id=session_id, 
        user_id="admin"
    )
    print(f"✅ Session '{session_id}' created.")

    # 4. Define a Test Scenario
    test_query = "User 9198765432 is reporting heavy buffering in Mumbai sector 4. Please investigate and fix."
    print(f"\nExample Input: '{test_query}'\n")

    # 5. Run the Agent
    user_msg = genai_types.Content(role="user", parts=[genai_types.Part(text=test_query)])

    # Pass the same user_id="admin" here
    async for event in runner.run_async(user_id="admin", session_id=session_id, new_message=user_msg):
        
        # Detect Tool Calls (When Orchestrator talks to Sub-Agents)
        if getattr(event, 'tool_call', None):
            print(f"   ⚙️  Orchestrator Decided: Call {event.tool_call.name}")
        
        # Detect Final Response
        if getattr(event, 'content', None) and event.content.parts:
            for part in event.content.parts:
                if getattr(part, 'text', None):
                    print(part.text, end="", flush=True)
    
    print("\n\n✅ Demo Complete.")

if __name__ == "__main__":
    asyncio.run(main())