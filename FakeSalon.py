import logging
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import openai, deepgram, silero

load_dotenv()

class SimpleAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent for a fake salon.
                Here are some basic details about the salon:
                - The salon offers haircuts, coloring, and styling.
                - Our hours are from 9 AM to 7 PM every day.
                - We offer a variety of services including deep conditioning, hair treatments, and scalp massages.
                If asked about the salon's services, respond with the above information.
                If you don't know the answer, trigger a 'request help' event.
            """,
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4o"),
            tts=openai.TTS(),
            vad=silero.VAD.load()
        )

    async def on_enter(self):
        response = self.session.generate_reply()
        if "request help" in response.lower():
            await self.trigger_request_help()
        else:
            logging.info(f"Agent responded: {response}")
    
    async def trigger_request_help(self):
        logging.info("Requesting help from external resources")

async def entrypoint(ctx: JobContext):
    await ctx.connect()

    session = AgentSession()
    agent = SimpleAgent()

    await session.start(
        agent=agent,
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
