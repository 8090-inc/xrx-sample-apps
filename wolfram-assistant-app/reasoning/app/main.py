from agent_framework import xrx_reasoning, initialize_llm_client, observability_decorator
from agent.executor import run_agent

# The rest of the code remains the same
llm_client = initialize_llm_client()


app = xrx_reasoning(run_agent=run_agent)()

