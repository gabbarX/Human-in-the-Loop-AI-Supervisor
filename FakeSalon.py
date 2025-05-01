import logging
import asyncio
import firebase_admin
from firebase_admin import credentials, db
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import openai, deepgram, silero
from livekit import rtc
from uuid import uuid4
from datetime import datetime, timedelta
import json

TIMEOUT_PERIOD = timedelta(minutes=5)

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("salon-agent")

cred = credentials.Certificate("firebase_credentials.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://human-in-the-loop-ai-default-rtdb.firebaseio.com'  
})
help_requests_ref = db.reference('HelpRequests')

class SimpleSalonAgent(Agent):
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
        question = self.session.input  
        answer = self.query_knowledge_base(question)
        
        if answer:
            await self.session.say(f"Here's what I found: {answer}")
            logger.info(f"Responded from knowledge base: {answer}")
        else:
            response = await self.session.generate_reply()
            if "request help" in response.lower():
                await self.trigger_request_help(question)
            else:
                await self.session.say(response)
                logger.info(f"Agent responded: {response}")
        
        if question.lower() == "show learned answers":
            learned_answers = self.view_learned_answers()
            await self.session.say(f"Learned Answers:\n{learned_answers}")

    async def trigger_request_help(self, question: str):
        help_request_id = str(uuid4())
        user_identity = self.session.participant.identity
        help_request_data = {
            'question': question,
            'status': 'pending',
            'user_identity': user_identity,
            'created_at': datetime.utcnow().isoformat(),
        }
        
        help_requests_ref.child(help_request_id).set(help_request_data)
        logger.warning(f"Help request created with ID: {help_request_id}")

        end_time = datetime.utcnow() + TIMEOUT_PERIOD
        while True:
            current_time = datetime.utcnow()
            if current_time > end_time:
                help_requests_ref.child(help_request_id).update({
                    'status': 'unresolved',
                    'resolved_at': current_time.isoformat(),
                })
                await self.session.say(f"Sorry, the answer to your question is still pending.")
                logger.warning(f"Help request {help_request_id} timed out and marked as unresolved.")
                break

            request_data = help_requests_ref.child(help_request_id).get()
            if request_data and request_data.get('status') == 'resolved':
                answer = request_data.get('answer')
                await self.session.say(f"Here's the answer to your question: {answer}")
                logger.info(f"Responded to the customer with answer: {answer}")
                break
            await asyncio.sleep(2)

    def update_knowledge_base(self, question, answer):
        knowledge_base_path = Path("knowledge_base.json")
        
        if knowledge_base_path.exists():
            with open(knowledge_base_path, 'r') as file:
                knowledge_base = json.load(file)
        else:
            knowledge_base = {}
        knowledge_base[question] = answer

        with open(knowledge_base_path, 'w') as file:
            json.dump(knowledge_base, file, indent=4)

        logger.info(f"Knowledge base updated with question: '{question}' and answer: '{answer}'")

    def view_learned_answers(self):
        knowledge_base_path = Path("knowledge_base.json")
        if knowledge_base_path.exists():
            with open(knowledge_base_path, 'r') as file:
                knowledge_base = json.load(file)
                learned_answers = "\n".join([f"Q: {q} - A: {a}" for q, a in knowledge_base.items()])
                if learned_answers:
                    logger.info(f"Learned Answers:\n{learned_answers}")
                    return learned_answers
                else:
                    logger.info("No learned answers yet.")
                    return "No learned answers yet."
        else:
            logger.info("Knowledge base file not found.")
            return "Knowledge base not found."

async def entrypoint(ctx: JobContext):
    await ctx.connect()
    session = AgentSession()
    agent = SimpleSalonAgent()
    await session.start(agent=agent, room=ctx.room)

    async def greet(participant: rtc.RemoteParticipant):
        logger.info(f"Greeting new participant: {participant.identity}")
        await agent.session.say("Hello! Welcome to our salon. How can I assist you today?")

    for participant in ctx.room.remote_participants.values():
        asyncio.create_task(greet(participant))

    ctx.room.on("participant_connected", lambda p: asyncio.create_task(greet(p)))

def supervisor_responds(help_request_id: str, supervisor_answer: str):
    help_requests_ref.child(help_request_id).update({
        'status': 'resolved',
        'answer': supervisor_answer,
        'resolved_at': datetime.utcnow().isoformat(),
    })
    logger.info(f"Supervisor resolved request {help_request_id} with answer: {supervisor_answer}")

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
