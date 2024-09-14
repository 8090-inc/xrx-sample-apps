from ..base import Node
import os
import asyncio
import logging
import json
from agent_framework import observability_decorator, initialize_async_llm_client, json_fixer
from agent.config import tools_desc
import openai
from pprint import pformat

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# set up llm
LLM_CLIENT = initialize_async_llm_client()
LLM_MODEL_ID = os.environ.get('LLM_MODEL_ID', '')

SYSTEM_PROMPT = '''\
You are an expert at deciding which tool to use to generate a response to the customer from the assistant. 
If the tool output is already in the conversation, don't use the tool again.
Keep track of previous tool calls and their results. If a tool call fails or produces unexpected results, do not repeat the same call without modification. Instead, analyze the error, report it to the user, and suggest an alternative action.
Maintain awareness of the full conversation history. Use this context to avoid repeating information or asking for details that have already been provided. Regularly summarize the current state of the order to ensure consistency.

## Tools
You have access to the following tools.

{tools}

## Historical Conversation

Here is the conversation so far:

{conversation}

## Output Format
You must return a perfectly formatted JSON object which can be serialized with the following keys:
- 'reason': a string explaining which tool is the correct tool for the situation.
- 'tool': a string representing the tool to use.

The 'reason' string should follow a pattern like below:
"The previous tool calls accomplished <diagnosis of previous tool calls here>. \
Based on these previous actions, the correct tool to call is <tool name here>. \
When I call this tool, I will use the following parameters: <description of tool parameter inputs here>"

If it is clear that a tool should not be called in this situation, simply state why in the 'reason' key \
and place a blank string "" in the 'tool' key.

## Rules
- Never assume an id input if it is not provided in the context or previous tool calls.
- Always use the exact values returned by the previous tools. Do not modify or create new values.
- Provide all information in the JSON object. Any other text is strictly forbidden.
- If you're unsure about any information, use the appropriate tool to verify rather than making assumptions.
'''.replace('{tools}', tools_desc)

TOOL_CACHE_PROMPT = '''
assistant:
### Tools Used Before Responding to Customer

{tool_output_cache}
'''

class ChooseTool(Node):
    def __init__(self, name, attributes):
        super().__init__(name, attributes)
        self.llm_client = LLM_CLIENT
        self.llm_model_id = LLM_MODEL_ID

    @observability_decorator('ChooseTool')
    async def process(self, messages: list, input: dict):
        try:
            logger.info(f"ChooseTool processing messages: {messages}")
            logger.info(f"ChooseTool processing input: {pformat(input, indent=2, width=100)}")
            
            # make a  copy of the system prompt
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
            single_system_prompt = SYSTEM_PROMPT.replace('{conversation}', conversation)

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

            # call the LLM
            logger.debug(f"ChooseTool input messages:\n{pformat(input_messages, indent=2, width=100)}")
            try:
                response = await self.llm_client.chat.completions.create(
                    model=self.llm_model_id,
                    messages=input_messages,
                    temperature=0.9,
                    response_format={ "type": "json_object" },
                )
                tool_output = json.loads(response.choices[0].message.content)
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON response. Attempting to fix with json_fixer.")
                tool_output = await json_fixer(response.choices[0].message.content)
            except openai.BadRequestError as e:
                if e.code == 'json_validate_failed':
                    logger.warning("JSON validation failed. Attempting to fix with json_fixer.")
                    tool_output = await json_fixer(e.response.json()['error']['failed_generation'])
                else:
                    raise e
            logger.info(f"ChooseTool tool_output: {tool_output}")

            # send the data back to the endpoint
            await asyncio.sleep(0) 
            yield {
                'node': self.id,
                'reason': tool_output['reason'],
                'output': tool_output['tool'],
                'memory': input.get('memory', {})
            }
            logger.info("ChooseTool finished processing")
        except Exception as e:
            logger.exception(f"An error occurred in ChooseTool")
            raise e

    async def get_successors(self, result: dict):
        successors = []
        tool = result.get('output', '')
        reason = result.get('reason', '')
        
        # format the tool if the model outputs a tool with parameters
        if '(' in tool:
            tool = tool.split('(')[0]

        if tool != "":
            successors.append(("IdentifyToolParams", {
                'tool': tool, 
                'reason': reason,
                'memory': result.get('memory', {})
            }))
        else:
            successors.append(("CustomerResponse", {
                'reason': reason,
                'memory': result.get('memory', {})
            }))
        return successors
