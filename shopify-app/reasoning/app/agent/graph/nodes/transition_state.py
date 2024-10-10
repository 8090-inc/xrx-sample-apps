from ..base import Node
import os
import asyncio
import logging
import json
from agent_framework import observability_decorator, initialize_async_llm_client, json_fixer, StateMachine
from agent.config import tools_desc
import openai
from pprint import pformat
import pdb

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# set up llm
LLM_CLIENT = initialize_async_llm_client()
LLM_MODEL_ID = os.environ.get('LLM_MODEL_ID', '')

SYSTEM_PROMPT = '''\
You are an expert at deciding which state machine state or flow to transition to next, given the current state, the conversation history, and \
the descriptions of the potential next states and flows. Only choose a state or flow if it appears in the list below. If you are transitioning \
between states, the name of your transition should begin with 'state_transition_'. If you are transitioning between flows, the name of your \
transition should begin with 'flow_transition_'.

Maintain awareness of the full conversation history. Use this context to avoid repeating information or asking for details that have already been provided. Regularly summarize the current state of the order to ensure consistency.

## Potential Next States and Flows
{state_machine_transitions}

## Historical Conversation

Here is the conversation so far:

{conversation}

## Flow and State Information

{flow_and_state_info}

## Output Format
You must return a perfectly formatted JSON object which can be serialized with the following keys:
- 'reason': a string explaining which tool is the correct tool for the situation.
- 'tool': a string representing the transition to make. This should be strictly limitited to the transitions listed under 'Potential Next States and Flows'.

The 'reason' string should follow a pattern like below:
"My current objective as defined by the state of the state machine is <current objective>. \
The objective of the current state has been met. Based on the context of my conversation with the customer, \
I am choosing to transition to <state or flow name here>. \"

Only use the state of the state machine listed in Flow and State Information to derive your objective; do not infer it on your own.

If it is clear that a transition shoudl not be made in this situation, simply state why in the 'reason' key \
and place a blank string "" in the 'tool' key.

## Rules
- Provide all information in the JSON object. Any other text is strictly forbidden.
'''


class TransitionState(Node):
    def __init__(self, name, attributes):
        super().__init__(name, attributes)
        self.llm_client = LLM_CLIENT
        self.llm_model_id = LLM_MODEL_ID

    @observability_decorator('TransitionState')
    async def process(self, messages: list, input: dict):
        try:
            logger.info(f"TransitionState processing messages: {messages}")
            logger.info(f"TransitionState processing input: {pformat(input, indent=2, width=100)}")
            
            # make a  copy of the system prompt
            single_system_prompt = SYSTEM_PROMPT

            # create the conversation variable
            conversation = ''.join([f"{i['role']}: {i['content']}\n" for i in messages])

            # add the conversation to the system prompt
            single_system_prompt = single_system_prompt.replace('{conversation}', conversation)

            # add the state machine prompt to the system prompt
            single_system_prompt = single_system_prompt.replace('{flow_and_state_info}', StateMachine.getStateMachinePrompt(input['memory']))

            # add state machine tool info to the system prompt
            single_system_prompt = single_system_prompt.replace('{state_machine_transitions}', StateMachine.getStateMachineTransitionCalls(input['memory']))


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
            logger.debug(f"TransitionState input messages:\n{pformat(input_messages, indent=2, width=100)}")
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
            logger.info(f"TransitionState tool_output: {tool_output}")

            # send the data back to the endpoint
            await asyncio.sleep(0) 

            yield {
                'node': self.id,
                'reason': tool_output['reason'],
                'output': tool_output['tool'],
                'memory': input.get('memory', {})
            }
            logger.info("TransitionState finished processing")
        except Exception as e:
            logger.exception(f"An error occurred in TransitionState")
            raise e

    async def get_successors(self, result: dict):
        successors = []
        tool = result.get('output', '')
        reason = result.get('reason', '')
        
        if tool != "":
            successors.append(("ExecuteTool", {
                'tool': tool,
                'parameters': {},
                'memory': result.get('memory', {})
            }))
        else:
            successors.append(("CustomerResponse", {
                'reason': reason,
                'memory': result.get('memory', {})
            }))
        return successors
