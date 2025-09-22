from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import SelectorGroupChat
from dotenv import load_dotenv
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
import os
from tools_ import search_code,run_trufflehog,run_gitleaks
from pydantic import RootModel
from typing import Dict, Any

load_dotenv()

class output_content_type(RootModel[Dict[str, Any]]):
    pass


model_client = AzureOpenAIChatCompletionClient(
   azure_deployment=os.getenv("AZURE_MODEL"),
    azure_endpoint=os.getenv("AZURE_MODEL_API_ENDPOINT"),
    model=os.getenv("AZURE_MODEL"),
    api_version=os.getenv("AZURE_API_VERSION"),
    api_key=os.getenv("AZURE_MODEL_API_KEY"),
    parparallel_tool_calls=True
)


github_search_agent = AssistantAgent(
    name="github_search_agent",
    system_message="""
    You are the GitHub search agent. Your job is to process user input and either:
    1. Generate a GitHub search query if the input is not a GitHub repository URL
    2. Return the URL if it's already a GitHub repository URL
    3. Provide a helpful response if the input is unclear
    
    Guidelines:
    - If the user query is a **brand, company, or product name** (e.g., "hdfc", "uber", "aws"), generate a search query using the search_code tool
    - If the user provides a GitHub repository URL, return that URL directly
    - If the input is unclear (like "hi"), ask for a specific brand name or repository URL and then TERMINATE
    - Always provide clear guidance on what the user should provide
    
    Examples:
    - Input: "hdfc" → Use search_code tool to generate search query
    - Input: "https://github.com/org/repo" → Return the URL
    - Input: "hi" → Ask for specific brand or repository URL, then TERMINATE
        """,
    model_client=model_client,
    tools=[search_code]
)


user_proxy_agent = UserProxyAgent(
    name="user_proxy_agent"
)

termination_condition=TextMentionTermination(
    text="TERMINATE"
)

leaks_agent=AssistantAgent(
    name="Code_Analysis_Team",
    description="""
    You are a leaks detection agent. You search for and analyze potential data leaks, security vulnerabilities, or exposed information based on user queries.Return the raw output
    If you cannot perform analysis handoff to summarizer_agent by saying 'HANDOFF TO summarizer_agent: No GitHub results found for this query'
    Run all the available tools to get the best results.
    """,
    model_client=model_client,
    tools=[run_trufflehog,run_gitleaks],
)


summarizer_agent = AssistantAgent(
    name="summarizer_agent",
    system_message="""
    You are the summarizer agent. Your task is to analyze and summarize the combined findings from multiple code analysis agents.
    
    You will receive raw JSON data from trufflehog and gitleaks agents. Your job is to:
    
    1. Parse and analyze the JSON data from both tools
    2. Extract meaningful information from the findings
    3. If no results found: explicitly hand off to leaks_agent by saying 'HANDOFF TO leaks_agent: No GitHub results found for this query'
    4. Provide a comprehensive summary that includes:
       - What sensitive information was found (e.g., AWS key, password, API tokens)?
       - Where (repository name, file path, line number)?
       - Who (if author metadata is available)?
       - When it was found (if available)?
       - Severity/impact level for each finding
       - Recommended actions (e.g., key rotation, contact owner, delete file history)
       - If no sensitive information was found, clearly state this
       - Provide actionable insights and next steps
    
    Format your output in a clear, structured manner that's easy to read and understand.

    End with TERMINATE
    """,
    model_client=model_client,
    max_tool_iterations=2
)

control_flow=SelectorGroupChat(
        participants=[user_proxy_agent, summarizer_agent,leaks_agent,github_search_agent],
        name="Final_Team",
        termination_condition=termination_condition,
        model_client=model_client,
        max_turns=10
    )

# Main execution function
async def run_secret_scan(query: str):
    """
    Run the code analysis workflow
    
    Args:
        query: str - The search query or repository URL to analyze
    """
    from autogen_agentchat.ui import Console
    
    await Console(control_flow.run_stream(
        task=f"query: {query}",
    ))
    




