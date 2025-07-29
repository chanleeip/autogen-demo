import os
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from autogen_agentchat.ui import Console
import asyncio
from dotenv import load_dotenv
from tools import run_nmap_scan,run_whois_lookup 



load_dotenv()


model_client = AzureOpenAIChatCompletionClient(
   azure_deployment=os.getenv("AZURE_MODEL"),
    azure_endpoint=os.getenv("AZURE_MODEL_API_ENDPOINT"),
    model=os.getenv("AZURE_MODEL"),
    api_version=os.getenv("AZURE_API_VERSION"),
    api_key=os.getenv("AZURE_MODEL_API_KEY"),
)

coordinator_agent = AssistantAgent(
    name="Coordinator_Agent",
    system_message="""
    You are the coordinator. Your role is to decide which agent should perform a task.
You do not perform tasks yourself. You initiate the correct agent and wait for their response.""",
    model_client=model_client,
)

recon_agent = AssistantAgent(
    name="Recon_Agent",
    system_message="""
    you are a recon agent that can use tools to get information about a target.
    railguard your actions and do not perform any actions that are not allowed.
Once done end it with TERMINATE""",
    model_client=model_client,
    model_client_stream=True,
    tools=[run_nmap_scan,run_whois_lookup],
    reflect_on_tool_use=True,
)

user_agent=UserProxyAgent(
    name="User_Agent",
)

termination_condition=TextMentionTermination(
    text="TERMINATE"
)

team=SelectorGroupChat(
    participants=[recon_agent,coordinator_agent,user_agent],
    model_client=model_client,
    termination_condition=termination_condition,
    max_turns=10
    )


async def run_conversation():
   await Console(team.run_stream(task=input("Enter your message: ")))  

if __name__ == "__main__":
    asyncio.run(run_conversation())