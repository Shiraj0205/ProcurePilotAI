
from langchain.agents import create_agent
from langchain_core.tools import tool
from backend.rag.llm import get_llm, extract_text_from_response
from backend.agent.tools import validate_fx_hedge

@tool
def approval_needed(transaction_amount: float) -> str:
    """Returns who must approve a transaction of this amount, in USD."""
    if transaction_amount > 1_000_000:
        return "CFO and Management Board"
    if transaction_amount > 250_000:
        return "Deapt. Head"
    return "Manager"


agent = create_agent(
    model=get_llm(),
    tools=[validate_fx_hedge, approval_needed],
    system_prompt="You are a procurement assistant. Always use your tool. Do not guess."
)

result = agent.invoke({"messages": [
    {
        "role": "user", 
        "content": "Who approves the purchases of USD 500000?"}
     ]
    }
)

for message in result["messages"]:
    calls = getattr(message, "tool_calls", None)
    print(f"{message.type}", 
          calls if calls else extract_text_from_response(message.content))


#---------------------------------------------------------------------------
# Root Folder: ProcurePilotAI

# How to run the file
# cmd.exe:
    # set PYTHONPATH=backend
    # uv run python -m validations.agent_test

#Or on one line: 
    # set "PYTHONPATH=backend" && uv run python -m validations.agent_test. 

#PowerShell:
    #$env:PYTHONPATH = "backend"; uv run python -m validations.agent_test

#---------------------------------------------------------------------------