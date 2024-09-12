from typing import List, Callable
import asyncio
import json
import os
import logging
import inspect

from .tools.generic_tools import get_current_weather, get_current_time, get_stock_price
from agent_framework import initialize_llm_client, observability_decorator

client = initialize_llm_client()
MODEL = os.environ['LLM_MODEL_ID']

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')

SYSTEM_PROMPT = """You are an AI agent that is designed to answer questions. 

## Rules
* Don't mention tool use directly.

## Output Style
Your output will be read aloud. This means you should always type out numbers, dates, times, and other numerical formats.

For example...
* if you want to say "12345", you should say "one two three four five"
* if you want to say "12:34 PM", you should say "twelve thirty four PM"
* if you want to say "$12.50", you should say "twelve dollars and fifty cents"
"""


@observability_decorator(name="run_agent")
async def run_agent(input_dict: dict):
    try:
        logging.info("Starting Agent Executor.")

        messages = input_dict['messages']
        session = input_dict['session']

        response = single_turn_agent(messages)
        response['session'] = session
        logging.info(f"Agent Output: {json.dumps(response)}")
        yield json.dumps(response)

    except Exception as e:
        logging.exception(f"An error occurred: {e}")

def extract_function_metadata(func: Callable) -> dict:
    """Extracts metadata from a function for tool definition."""
    sig = inspect.signature(func)
    parameters = {
        name: {
            "type": "string",
            "description": f"The {name.replace('_', ' ')}"
        }
        for name, param in sig.parameters.items()
    }
    return {
        "name": func.__name__,
        "description": func.__doc__ or f"Get the {func.__name__.replace('_', ' ')}",
        "parameters": {
            "type": "object",
            "properties": parameters,
            "required": list(parameters.keys())
        }
    }

def single_turn_agent(messages: List[dict]) -> str:

    system_prompt = {
        "role": "user",
        "content": SYSTEM_PROMPT
    }
    assistant_prompt = {
        "role": "assistant",
        "content": "Understood! I will answer your questions with the exact output style you have specified."
    }
    messages.insert(0, assistant_prompt)
    messages.insert(0, system_prompt)


    original_message_length = len(messages)

    tools_dict = {
        "get_current_weather": get_current_weather,
        "get_current_time": get_current_time,
        "get_stock_price": get_stock_price,
    }

    tools = [
        {
            "type": "function",
            "function": extract_function_metadata(func)
        }
        for func in tools_dict.values()
    ]

    response = client.chat.completions.create(
        model=os.environ['LLM_MODEL_ID'],
        messages=messages,
        tools=tools,
        tool_choice="auto",
        max_tokens=4096
    )
    response_message = response.choices[0].message
    if response_message.content:
        messages.append(
            {
                "role": "assistant",
                "content": response_message.content
            }
        )
    tool_calls = response_message.tool_calls

    if tool_calls:
        available_functions = tools_dict
        response_message_dict = response_message.model_dump()
        response_message_dict.pop("function_call", None)
        messages.append(response_message_dict)
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            function_response = function_to_call(**function_args)
            messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                }
            )
        
        second_response = client.chat.completions.create(
            model=MODEL,
            messages=messages
        )
        messages.append(
            {
                "role": "assistant",
                "content": second_response.choices[0].message.content
            }
        )

    # use the "node" and "output" fields to ensure a response is sent to the front end through the xrx orchestrator
    out = {
        "messages": messages[original_message_length:],
        "node": "CustomerResponse",
        "output": messages[-1]['content'],
    }
    return out
