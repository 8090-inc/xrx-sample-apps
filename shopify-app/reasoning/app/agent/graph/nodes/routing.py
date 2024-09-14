from ..base import Node
from datetime import datetime
import os
import logging
import asyncio
import json
from agent_framework import observability_decorator, initialize_async_llm_client, json_fixer
from agent.config import tools_dict, tool_param_desc
from agent.config import store_info, customer_service_task
import openai
import copy

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# set up llm
LLM_CLIENT = initialize_async_llm_client()
LLM_MODEL_ID = os.environ.get('LLM_MODEL_ID', '')

SYSTEM_PROMPT = '''\
You an expert at determining if you have enough information to generate a response to the user from the assistant.

## Store information
{store_info}

## Customer Service Task
{customer_service_task}

## Tools
You have access to the following tools:
{tools}

## Conversation

Here is the conversation so far:

{conversation}

## Output Format
You must return a perfectly formatted JSON object which can be serialized with the following keys:
- 'reason': a string explaining why you chose to either call a tool or respond to the customer.
- 'next-action': a string representing the next action to take. This will be 'call-tool' or 'respond-to-customer'.

The 'reason' string should follow a logical step by step pattern like below:
"The historical conversation showed <diagnosis of conversation so far>. \
The previous tool calls accomplished <diagnosis of tool calls so far>. \
Based on these previous tool calls and all available information, I am choosing to
<description of the tool call or response to the customer>"

Your JSON output should not have more than the two keys 'reason' and 'next-action'.

## Rules
Whenever a customer is asking questions about something in the shop, you should only respond if:
1. You are certain of the answer based on the output of tools
2. You have tried to find the information via tools and it is not available.
'''.replace('{tools}','\n'.join([f"{tool}({', '.join([f'{desc}' for param, desc in tool_param_desc[tool].items()])})" for tool in tools_dict.keys()]) )
SYSTEM_PROMPT = SYSTEM_PROMPT.replace('{store_info}', store_info).replace('{customer_service_task}', customer_service_task)

TOOL_CACHE_PROMPT = '''
assistant:
### Tools Used Before Responding to Customer

{tool_output_cache}
'''

class Routing(Node):
    def __init__(self, name, attributes):
        super().__init__(name, attributes)
        self.llm_client = LLM_CLIENT
        self.llm_model_id = LLM_MODEL_ID
    
    @observability_decorator('Routing')
    async def process(self, messages: list, input: dict):
        try:
            logger.info(f"Router processing messages: {messages}")
            logger.info(f"Router processing input: {input}")

            # make a copy of the system prompt
            single_system_prompt = SYSTEM_PROMPT

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
                routing_output = json.loads(response.choices[0].message.content)
            except openai.BadRequestError as e:
                if e.code == 'json_validate_failed':
                    routing_output = await json_fixer(e.response.json()['error']['failed_generation'])
                else:
                    raise e
            logger.info(f"Routing output: {routing_output}")

            await asyncio.sleep(0)
            yield {
                'node': self.id,
                'output': routing_output.get('next-action', ''),
                'reason': routing_output.get('reason', ''),
                'memory': input.get('memory', {})
            }
            logger.info("Router finished processing")
        except Exception as e:
            logger.exception(f"An error occurred in Routing")
            raise e

    async def get_successors(self, result: dict):
        successors = []
        next_action = result.get('output', [])
        memory = result.get('memory', {})

        if 'respond-to-customer' in next_action:
            successors.append(("CustomerResponse", copy.deepcopy({
                'memory': memory
            })))
        
        # when a tool is called, we need to tell the customer that we are working on their request
        tool_output_cache = memory.get('tool-output-cache', [])
        if len(tool_output_cache) == 0:
            memory['task-description-to-customer'] = True
        else:
            memory['task-description-to-customer'] = False

        if 'call-tool' in next_action:
            successors.append(("TaskDescriptionResponse", copy.deepcopy({
                'memory': memory
            })))
            successors.append(("ChooseTool", copy.deepcopy({
                'memory': memory
            })))
        
        return successors