from ..base import Node
import os
import asyncio
import logging
import json
import asyncio
from agent_framework import observability_decorator, initialize_async_llm_client, json_fixer
from agent.config import tools_dict, tool_param_desc
import openai

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# set up llm
LLM_CLIENT = initialize_async_llm_client()
LLM_MODEL_ID = os.environ.get('LLM_MODEL_ID', '')

SYSTEM_PROMPT = '''\
You are an expert technical communicator who can read tool outputs and describe them with perfect english.
Your job is to convert the result of a tool to a plain english description. You will also have access to the \
messages between the User and the Agent. Use these messages to influence your description. Do not worry if a tool call \
result is not pertinent to the conversation, you are still in charge of making a description for all of the information \
in the tool call result.

Integer values for products, orders, and carts should always be included in the description. These are critical for \
downstream tasks, so the description should include the IDs. Any mistake on the copying of these IDs in your description \
will result in a catastrophic system failure. Make sure to double check all IDs in your reasoning output before \
providing them in the description.

## Conversation

Here is the conversation so far:

{conversation}

## Tool Call Result

Tool: {tool}

Input: {tool_input}

Output:
{tool_output}

## Output Format:
You must return a perfectly formatted JSON object which can be serialized with the following keys:
- 'reason': a string explaining why you chose the value for description.
- 'description': the natural language description of the tool call result following the sentence structure \
"Calling <tool here> with input <tool_input> returned <tool_output>. Relevant information to the conversation \
might include <relevant information>".

## Rules
- Do not describe the tool in the 'description'.
- Your 'description' string in the JSON response 
should not include a dictionary of information, it should read like a sentence a human would understand.
- Ensure that all IDs are included in the 'description' if they are produced in the tool output.
- All information provided in the tool output must be included in the 'description'.
- Your response must ONLY be JSON output. Any other text is strictly forbidden.
'''

TOOL_CACHE_PROMPT = '''
assistant:
### Tools Used Before Responding to Customer

{tool_output_cache}
'''

class ConvertNaturalLanguage(Node):

    def __init__(self, name, attributes):
        super().__init__(name, attributes)
        self.llm_client = LLM_CLIENT
        self.llm_model_id = LLM_MODEL_ID

    @observability_decorator('ConvertNaturalLanguage')
    async def process(self, messages: list, input: dict):
        try:
            logger.info(f"ConvertNaturalLanguage messages: {messages}")
            logger.info(f"ConvertNaturalLanguage input: {input}")

            # add the tool information to the system prompts
            tool = input['tool']
            tool_output_str = json.dumps(input['output'])
            tool_input_str = json.dumps(input['parameters'])
            single_system_prompt = SYSTEM_PROMPT.replace('{tool}', tool)
            single_system_prompt = single_system_prompt.replace('{tool_output}', tool_output_str)
            single_system_prompt = single_system_prompt.replace('{tool_input}', tool_input_str)

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
                convert_to_natural_language_output = json.loads(response.choices[0].message.content)
            except openai.BadRequestError as e:
                if e.code == 'json_validate_failed':
                    convert_to_natural_language_output = await json_fixer(e.response.json()['error']['failed_generation'])
                else:
                    raise e

            logger.info(f"ConvertNaturalLanguage output: {convert_to_natural_language_output}")

            tool_output_cache = input.get('memory', {}).get('tool-output-cache', [])
            tool_output_cache.append({
                'tool': tool,
                'input': tool_input_str,
                'output': tool_output_str,
                'description': convert_to_natural_language_output.get('description', ''),
            })
            logger.info(f"ConvertNaturalLanguage tool_output_cache: {tool_output_cache}")

            memory = input.get('memory', {})
            memory['tool-output-cache'] = tool_output_cache
            logger.info(f"ConvertNaturalLanguage memory: {memory}")

            await asyncio.sleep(0)
            yield {
                'node': self.id,
                'reason': convert_to_natural_language_output.get('reason', ''),
                'tool': input.get('tool', ''),
                'output': convert_to_natural_language_output.get('description', ''),
                'memory': memory
            }

            logger.info("ConvertNaturalLanguage finished processing")
        except Exception as e:
            logger.exception(f"An error occurred in ConvertNaturalLanguage")
            raise e

    async def get_successors(self, result: dict):
        successors = []
        successors.append(("Routing", {
            'cnl_output': {
                'tool': result.get('tool', ''),
                'output': result.get('output',{})
            },
            'memory': result.get('memory',{})
        }))
        return successors
