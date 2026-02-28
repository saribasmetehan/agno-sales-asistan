from pathlib import Path
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.db.sqlite import SqliteDb

from prompts.prompt import guardrail_prompt
from tools.utils import call_llm

def check_guardrails(query: str) -> str:
    """
    Satış Asistanı için Güvenlik Kontrolü Tool'udur.
    Bu tool her kullanıcı sorgusunun güvenli olup olmadığını kontrol eder. Her zaman ilk çalışması gereken tool'dur.
    """
    try:
        result = call_llm(
            user_prompt=query,
            system_prompt=guardrail_prompt,
        )
        return result.strip()
    except Exception as e:
        return f"UNSAFE: Error: {str(e)}"

GUARDRIAL_AGENT = Agent(
    name="GUARDRIAL_AGENT",
    model=OpenAIChat(id="gpt-4o"),
    db=SqliteDb(db_file=str(Path(__file__).parent.parent / "data" / "agno_shared.db")),
    tools=[
        check_guardrails
    ],
    instructions=guardrail_prompt,
    add_history_to_context=True,
    markdown=True,
)
