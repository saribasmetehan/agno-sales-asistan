from agno.team import Team
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.db.sqlite import SqliteDb
from pathlib import Path
from agents.agent_playbook import PlaybookAgent
from agents.agent_sql import SQLAgent
from agents.agent_guardrial import GUARDRIAL_AGENT
from prompts.prompt import orchestrator_prompt

DB_PATH = Path(__file__).parent.parent / "data" / "agno_shared.db"

team = Team(
    name="Sales Team",
    members=[GUARDRIAL_AGENT, PlaybookAgent, SQLAgent],
    model=OpenAIChat(id="gpt-4o"),
    db=SqliteDb(db_file=str(DB_PATH)),
    instructions=orchestrator_prompt,
    add_history_to_context=True,
    markdown=True,
)

