from .context_manager import set_session, session_var
import asyncio
import json
from agent_framework import observability_decorator
from .graph.main import agent_graph
import logging
import traceback
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')

observability_library = os.getenv("LLM_OBSERVABILITY_LIBRARY", 'none').lower()

@observability_decorator(name="run_agent")
async def run_agent(input_dict: dict):

    if observability_library == "langfuse":
        from langfuse.decorators import langfuse_context, observe
        langfuse_context.update_current_trace(
            session_id=input_dict['session'].get('guid')
        )
        print('SESSION GUID:', input_dict['session'].get('guid'))
    
    # Look up the session information and ensure there is a cart id to work with
    session_data = input_dict['session']
    messages = input_dict['messages']
    action = input_dict.get('action', {})
    task_id = input_dict.get('task_id', '')
    
    logging.info("Session data and messages received.")

    # Use the context manager to set the session for the planning expert
    with set_session(session_data):
        try:
            logging.info("Starting to enter the graph")

            # place graph execution here
            async for result in agent_graph(messages, task_id, action, {}):
                if 'error' in result:
                    logging.error(f"Error in graph traversal: {result}")
                    yield json.dumps(result)
                    return
                yield format_result_to_output(result)

        except Exception as e:
            logging.exception(f"Error occurred in the agent graph")
            error_traceback = traceback.format_exc()
            yield json.dumps({
                'error': str(e),
                'traceback': error_traceback
            })
            raise e


def format_result_to_output(result):
    logging.info(f"Starting output formatting...")
    try:
        tool_prompt_start = "### Tools Used Before Responding to Customer\n\n"
        response_prompt_start = "\n\n### Audio Response to Customer\n\n"
        result = json.loads(result)
        if result.get('memory', {}).get('tool-output-cache', []):
            tool_output_cache = result.get('memory', {}).get('tool-output-cache', [])
            tool_output_cache_str = ''.join([
                f"* {i['tool']}: {i['description']}\n"
                for i in tool_output_cache
            ])
            tool_output_cache_str = tool_prompt_start + tool_output_cache_str
            messages_output = [
                {
                    "role": "assistant",
                    "content": tool_output_cache_str
                },
            ]
        else:
            messages_output = [
                {
                    "role": "assistant",
                    "content": ""
                }
            ]
        
        if result.get('node', '') == 'CustomerResponse':
            messages_output[-1]['content'] += response_prompt_start + result.get('output', '')
    
    except Exception as e:
        
        logging.exception(f"An error occurred during format_result_to_output")
        raise e

    return json.dumps({
        'messages': messages_output,
        'session': session_var.get(),
        'node': result.get('node', ''),
        'output': result.get('output', ''),
        'reason': result.get('reason', ''),
    })
