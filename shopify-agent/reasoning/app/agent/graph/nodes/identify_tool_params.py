from ..base import Node
import os
import logging
import json
import asyncio
from agent_framework import observability_decorator, initialize_async_llm_client, json_fixer
from agent.config import tools_dict, tool_param_desc
import openai
from pprint import pformat

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# set up llm
LLM_CLIENT = initialize_async_llm_client()
LLM_MODEL_ID = os.environ.get('LLM_MODEL_ID', '')

SYSTEM_PROMPT = '''\
You an expert at identifying and mapping parameters from a conversation and memory to a function call.

## Tool to identify:
{tool}

## Reason for choosing this tool:
{reason}

## Parameters required to identify:
{parameters}

## Conversation so far:
{conversation}

## Output Format
You must return a perfectly formatted JSON object which can be serialized with the following keys:
- 'reason': a string explaining why you chose the value for each parameter.
- 'parameters': a dictionary representing the parameter keys and values.

The 'parameters' key must contain the exact type of parameter as defined in the tool description. \
For instance, if the tool description specifies an integer, you must return a single integer. \
Returning a list of integers would be incorrect because the tool expects a single integer, not a list of integers.

For example, if the parameters required to identify are "product_id: int" and "product_name: string", you must return:

- Correct: { "product_id": 5, "product_name": "Pizza" }
- Incorrect: { "product_id": [5, 10, 15], "product_name": "Pizza" }
'''

TOOL_CACHE_PROMPT = '''
assistant:
### Tools Used Before Responding to Customer

{tool_output_cache}
'''


class IdentifyToolParams(Node):

    def __init__(self, name, attributes):
        super().__init__(name, attributes)
        self.llm_client = LLM_CLIENT
        self.llm_model_id = LLM_MODEL_ID

    @observability_decorator('IdentifyToolParams')
    async def process(self, messages: list, input: dict):
        try:
            logger.info(f"IdentifyToolParams for tool {input} processing messages: {messages}")

            tool = input.get('tool', '')
            reason = input.get('reason', 'No reason provided')  # Get the reason from input

            if len(tool_param_desc[tool].items()) > 0:
                tool_param_desc_str = ''.join([f"{v}\n" for k, v in tool_param_desc[tool].items()]) or 'no parameters required'
                single_system_prompt = SYSTEM_PROMPT.replace('{parameters}', tool_param_desc_str).replace('{tool}', tool).replace('{reason}', reason)
                
                # retrieve all tool calls which have been made and make the string if there are any
                tool_output_cache = input.get('memory', {}).get('tool-output-cache', [])

                # create the conversation variable
                conversation = ''.join([f"{i['role']}: {i['content']}\n" for i in messages])

                # add tool call cache to the conversation if it exists
                if len(tool_output_cache) > 0:
                    tool_output_cache_str = ''.join([f"* {i['tool']}: {i['description']}\n" for i in tool_output_cache])
                    single_tool_cache_prompt = TOOL_CACHE_PROMPT.replace('{tool_output_cache}', tool_output_cache_str)
                    conversation += single_tool_cache_prompt

                # add the conversation to the system prompt
                single_system_prompt = single_system_prompt.replace('{conversation}', conversation)
                logger.info(f"single_system_prompt: {single_system_prompt}")

                # create the messages format
                input_messages = [
                    {
                        "role": "system",
                        "content": single_system_prompt
                    }
                ]
                input_messages.append({
                    "role": "user",
                    "content": '<awaiting your next JSON response>'
                })

                try:
                    response = await self.llm_client.chat.completions.create(
                        model=self.llm_model_id,
                        messages=input_messages,
                        temperature=0.9,
                        response_format={ "type": "json_object" },
                    )
                    identify_tool_params_output = json.loads(response.choices[0].message.content)
                except openai.BadRequestError as e:
                    if e.code == 'json_validate_failed':
                        identify_tool_params_output = await json_fixer(e.response.json()['error']['failed_generation'])
                    else:
                        raise e
            else:
                identify_tool_params_output = {}
            logger.info(f"IdentifyToolParams output: {identify_tool_params_output}")

            await asyncio.sleep(0)
            yield {
                'node': self.id,
                'reason': identify_tool_params_output.get('reason', ''),
                'tool': input.get('tool', ''),
                'output': identify_tool_params_output.get('parameters', {}), 
                'memory': input.get('memory', {})
            }
            logger.info("IdentifyToolParams finished processing")
        except Exception as e:
            logger.exception(f"An error occurred in IdentifyToolParams")
            raise e

    async def get_successors(self, result: dict):
        successors = []
        successors.append(("ExecuteTool", {
            'tool': result.get('tool', ''),
            'parameters': result.get('output', {}),
            'memory': result.get('memory', {})
        }))
        return successors
