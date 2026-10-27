"""LangChain v1 middleware for the specialist agents.

Middleware wraps the agent loop (model call -> tool calls -> model call ...) without
touching the agent's prompt or tools. Think of it as airport security around the agent:
every request and every tool call passes through these checks, in list order.

    request ─► [PII redaction] ─► [model call limit] ─► [model retry] ─► Gemini
                                                                       │ wants a tool
    tool    ◄─ [tool call log] ◄─ [tool call limit] ◄─ [tool retry]  ◄─┘

Built-in middleware used here (from langchain.agents.middleware):
  * PIIMiddleware            - redacts e-mail addresses / card numbers before they reach the LLM
  * ModelCallLimitMiddleware - stops an agent that loops (cost guard)
  * ToolCallLimitMiddleware  - caps how many tools one audit phase can call
  * ModelRetryMiddleware     - retries Gemini on transient errors (429 / 503) with backoff
  * ToolRetryMiddleware      - retries flaky tools (e.g. the live FX-rate API)
Custom middleware written here:
  * log_tool_calls           - one structured log line per tool call: name, args, duration, outcome
"""

import time
from langchain.agents.middleware import (
    AgentMiddleware,
    ModelCallLimitMiddleware,
    ModelRetryMiddleware,
    PIIMiddleware,
    ToolCallLimitMiddleware,
    ToolRetryMiddleware,
    wrap_tool_call
    )

from config.settings import settings
from logger import GLOBAL_LOGGER as logger

@wrap_tool_call
def log_tool_calls(request, handler):
    """Log tool calls for monitoring and debugging."""
    tool_name = request.tool_call["name"]
    logger.info(f"Tool call started: {tool_name}")
    started_at = time.perf_counter()
    try:
        result = handler(request)
    except Exception:
        logger.exception("Tool call failed", tool=tool_name,
                         duration_ms=round((time.perf_counter() - started_at) * 1000))
        raise

    logger.info("Tool call finished", tool=tool_name,
             duration_ms=round((time.perf_counter() - started_at) * 1000),
             preview=str(getattr(result, "content", result))[:200])
    return result

def build_agent_middleware() -> list[AgentMiddleware]:
    """Build the middleware stack for the specialist agents.""" 
    return [
        # 1. Privacy: purchase requests can contain contact e-mails or card numbers
        PIIMiddleware("email", strategy="redact", apply_to_input=True),
        PIIMiddleware("credit_card", strategy="mask", apply_to_input=True),
        # 2. Guardrails: prevent runaway costs or infinite loops
        ModelCallLimitMiddleware(run_limit=settings.agent_max_model_calls, exit_behavior="end"),
        ToolCallLimitMiddleware(run_limit=settings.agent_max_tool_calls, exit_behavior="continue"),
        # 3. Reliability: retry transient errors (429 / 503) with exponential backoff
        ModelRetryMiddleware(max_retries=settings.agent_max_retries, initial_delay=1.0),
        ToolRetryMiddleware(max_retries=settings.agent_max_retries, initial_delay=0.5),
        # 4. Observability: log every tool call with name, args, duration, outcome
        log_tool_calls
    ]
