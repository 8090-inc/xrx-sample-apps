from ..base import Node
import os
import asyncio
import logging
import json
import asyncio
from agent_framework import observability_decorator, initialize_async_llm_client, json_fixer, StateMachine
import openai
from agent.config import store_info, customer_service_task

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# set up llm
LLM_CLIENT = initialize_async_llm_client()
LLM_MODEL_ID = os.environ.get('LLM_MODEL_ID', '')

SYSTEM_PROMPT = '''\
Your job is to ensure that the user's query and agent's response are aligned with your \
current objective, as defined by the current state of the state machine.

The information you have about the state of the state machine is as follows:

{flow_and_state_info}

The user's query is as follows:

{user_query}

The agent's response is as follows:

{agent_response}

## Output Format
You must return a perfectly formatted JSON object which can be serialized with the following keys:
- 'checkPassed': if the user query and/or the agent response are not related to your current \
objective, this should be 'FAIL'. Otherwise, this should be 'PASS'.
- 'reason': a string explaining why the check passed or failed.
- 'response': if the check failed, this should be a message that informs the user that you are \ 
unable to help with their request and gently moves the focus back towards the current objective. \
If the check passed, this should be an empty string.

The 'reason' string should follow a logical step by step pattern like below:

"My current objective as defined by the state of the state machine is <current objective>. \
Is the user's question related to the current objective? <true or false>. \
Is my response to the user related to the current objective? <true or false>. \
Based on the information above, I conclude that the check <passed or failed>."
'''

class StateMachineGuardrailsCheck(Node):
    def __init__(self, name, attributes):
        super().__init__(name, attributes)
        self.llm_client = LLM_CLIENT
        self.llm_model_id = LLM_MODEL_ID

    @observability_decorator('StateMachineGuardrailsCheck')
    async def process(self, messages: list, input: dict):
        try:
            logger.info(f"StateMachineGuardrailsCheck processing messages: {messages}")

            # make a single system prompt which has the conversation if needed
            single_system_prompt = SYSTEM_PROMPT

            # add the state machine prompt to the system prompt
            single_system_prompt = single_system_prompt.replace('{flow_and_state_info}', StateMachine.getStateMachinePrompt(input['memory']))

            single_system_prompt = single_system_prompt.replace('{user_query}', [m['content'] for m in messages if m['role'] == 'user'][-1])

            single_system_prompt = single_system_prompt.replace('{agent_response}', input['agentResponse'])

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
            try:
                response = await self.llm_client.chat.completions.create(
                    model=self.llm_model_id,
                    messages=input_messages,
                    temperature=0.9,
                    response_format={ "type": "json_object" },
                )
                customer_response_output = json.loads(response.choices[0].message.content)
            except openai.BadRequestError as e:
                if e.code == 'json_validate_failed':
                    customer_response_output = await json_fixer(e.response.json()['error']['failed_generation'])
                else:
                    raise e

            await asyncio.sleep(0)
            c_response = customer_response_output['response']

            yield {
                'node': self.id,
                'reason' : customer_response_output['reason'],
                'output': c_response if c_response else input['agentResponse'],
                'memory': input.get('memory', {})
            }
            logger.info("StateMachineGuardrailsCheck finished processing")
        except Exception as e:
            logger.exception(f"An error occurred in StateMachineGuardrailsCheck")
            raise e

    async def get_successors(self, result: dict):
        return []
