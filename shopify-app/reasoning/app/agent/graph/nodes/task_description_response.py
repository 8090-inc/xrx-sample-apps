from ..base import Node
import os
import asyncio
import logging
import json
from agent_framework import observability_decorator, initialize_async_llm_client, json_fixer
from agent.config import tools_dict, tool_param_desc
import openai
from datetime import datetime, timedelta

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# set up llm
LLM_CLIENT = initialize_async_llm_client()
LLM_MODEL_ID = os.environ.get('LLM_MODEL_ID', '')

SYSTEM_PROMPT = '''\
Your job is to generate a brief, personalized waiting message for the customer.
The message should be vague about the specific tasks that you will be performing in the future \
but should acknowledge that you are working on their request. Use the conversation context and \
previous tool calls (if provided) to make the response more relevant and personal.
Make it five words or less.

## Tools
Here are the tools which you will be using in the future to help solve the customer's request.
You should never tell the customer about the tools or mention them. Only use this \
information to help you generate the waiting message to the customer response.

{tools}

## Conversation

Here is the conversation so far:

{conversation}

## Tone and Style
Make sure your response is extremely human like. No one would say something like "processing this request" or "I'm working on this request". \
They would say things like "Ok one second" or "let me check on that" or "let me check that order quickly". Use this style in your response.

## Output Format:
You must return a perfectly formatted JSON object which can be serialized with the following keys:
- 'reason': a string explaining why you chose this waiting message.
- 'response': the waiting message for the customer.

Keep the response brief, friendly, and reassuring. Do not provide specific details about
the tasks being performed, but you may vaguely reference the type of information being gathered
or actions being taken if it's relevant to the customer's last request.

You do not have any other teammates working on the task, so do not reference anyone but yourself.

If tool calls have been made, use this information to make your response more specific
without revealing exact details of the operations being performed.
'''.replace('{tools}','\n'.join([f"{tool}({', '.join([f'{desc}' for param, desc in tool_param_desc[tool].items()])})" for tool in tools_dict.keys()]) )

TOOL_CACHE_PROMPT = '''
assistant:
### Tools Used Before Responding to Customer

{tool_output_cache}
'''

class TaskDescriptionResponse(Node):
    def __init__(self, name, attributes):
        super().__init__(name, attributes)
        self.llm_client = LLM_CLIENT
        self.llm_model_id = LLM_MODEL_ID

    @observability_decorator('TaskDescriptionResponse')
    async def process(self, messages: list, input: dict):
        try:
            logger.info(f"TaskDescriptionResponse processing messages: {messages}")

            should_proceed = input.get('memory', {}).get('task-description-to-customer', False)
            if not should_proceed:
                logger.info(f"TaskDescriptionResponse not responding to customer based on memory: {input.get('memory', {})}")
                return
            logger.info(f"TaskDescriptionResponse responding to customer based on memory: {input.get('memory', {})}")

            # start with a blank system prompt
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
                    temperature=0.7,
                    response_format={ "type": "json_object" },
                )
                task_description_output = json.loads(response.choices[0].message.content)
            except openai.BadRequestError as e:
                if e.code == 'json_validate_failed':
                    task_description_output = await json_fixer(e.response.json()['error']['failed_generation'])
                else:
                    raise e

            await asyncio.sleep(0)
            yield {
                'node': self.id,
                'reason': task_description_output['reason'],
                'output': task_description_output['response'],
                'memory': input.get('memory', {})
            }
            logger.info("TaskDescriptionResponse finished processing")
        except Exception as e:
            logger.exception(f"An error occurred in TaskDescriptionResponse")
            raise e

    async def get_successors(self, result: dict):
        return []
