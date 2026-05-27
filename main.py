import os
import asyncio
from dotenv import load_dotenv
load_dotenv()

os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
from agent.shrink_agent import shrink_agent

async def run():
    print("\n🔍 Shrink Agent starting...\n")

    session_service = InMemorySessionService()
    runner = Runner(
        agent=shrink_agent,
        app_name="shrink_agent",
        session_service=session_service
    )

    session = await session_service.create_session(
        app_name="shrink_agent",
        user_id="loss_prevention"
    )

    message = Content(
        role="user",
        parts=[Part(text="Investigate STORE-184 for suspicious activity in the last 200 hours. Check all data sources and save any confirmed incidents.")]
    )

    print("Agent reasoning:\n" + "=" * 50)

    async for event in runner.run_async(
        user_id="loss_prevention",
        session_id=session.id,
        new_message=message
    ):
        if hasattr(event, 'content') and event.content:
            for part in event.content.parts:
                if hasattr(part, 'function_call') and part.function_call:
                    print(f"\n🔧 Tool call: {part.function_call.name}")
                elif hasattr(part, 'text') and part.text:
                    print(part.text)

        if event.is_final_response():
            print("\n" + "=" * 50)
            print("\n✅ Investigation complete.")

if __name__ == "__main__":
    asyncio.run(run())