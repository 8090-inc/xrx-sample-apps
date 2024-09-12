from typing import List, Dict
import json
import logging
from agent_framework import initialize_llm_client, observability_decorator

import os
from .tools import generic_tools

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')

client = initialize_llm_client()
MODEL = os.environ['LLM_MODEL_ID']

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
async def run_agent(input_dict: Dict[str, any]) -> None:
    """
    Main entry point for the agent. Processes input and yields a JSON response.

    Args:
    input_dict (Dict[str, any]): Dictionary containing 'messages' and 'session' data.

    Yields:
    str: JSON-encoded response from the agent.
    """
    try:
        logging.info("Starting Agent Executor.")
        messages = input_dict['messages']
        session = input_dict['session']

        response = await single_turn_agent(messages)
        response['session'] = session
        logging.info(f"Agent Output: {json.dumps(response)}")
        yield json.dumps(response)

    except Exception as e:
        logging.exception(f"An error occurred: {e}")

async def single_turn_agent(messages: List[Dict[str, str]]) -> Dict[str, any]:
    """
    Processes a single turn of conversation with the agent.

    Args:
    messages (List[Dict[str, str]]): List of message dictionaries.

    Returns:
    Dict[str, any]: Dictionary containing the agent's response.
    """
    system_prompt = {
        "role": "user",
        "content": SYSTEM_PROMPT
    }
    assistant_prompt = {
        "role": "assistant",
        "content": "Ok. I will answer your questions with the exact output style you have specified."
    }

    messages = [system_prompt, assistant_prompt] + messages
    original_message_length = len(messages)

    # Defines a tool that the language model can use. In this case, it's the ask_wolfram_assistant function that
    #  relies on the generic_tools module to get an educational response to a question.
    tools = [{
        "type": "function",
        "function": {
            "name": "ask_wolfram_assistant",
            "description": "Get an educational response to a question",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The question to ask"
                    }
                },
                "required": ["question"]
            }
        }
    }]

    # First LLM call to decide whether to use the tool or not.
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=tools,
        tool_choice="auto",
        max_tokens=4096
    )

    # Appends the response to the messages list.
    response_message = response.choices[0].message
    messages.append({"role": "assistant", "content": response_message.content or ""})

    # If the response contains a tool call, LLM will invoke the tool and appends the response to the messages list.
    if response_message.tool_calls:
        for tool_call in response_message.tool_calls:
            function_args = json.loads(tool_call.function.arguments)
            function_response = await ask_wolfram_assistant(**function_args)
            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": "ask_wolfram_assistant",
                "content": json.dumps(function_response),
            })
        
        # Second LLM call that merges the tool call response with a polished response.
        second_response = client.chat.completions.create(
            model=MODEL,
            messages=messages
        )
        messages.append({
            "role": "assistant",
            "content": second_response.choices[0].message.content
        })

    # Return the final response in the format desired by the orchestrator.
    return {
        "messages": [messages[-1]],
        "node": "CustomerResponse",
        "output": messages[-1]['content'],
    }


async def ask_wolfram_assistant(question: str) -> str:
    """
    Retrieves an wolfram response for a given question.

    Args:
    question (str): The question to be answered.

    Returns:
    str: The wolfram response.
    """
    if not question:
        return "No question provided"

    logging.info(f"QUESTION: {question}")
    answer = generic_tools.get_wolfram_response(question)
    logging.info(f"ANSWER: {answer}")
    return answer