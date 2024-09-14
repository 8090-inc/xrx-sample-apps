from ..base import Node
import os
import asyncio
import logging
import json
import asyncio
from agent_framework import observability_decorator, initialize_async_llm_client, json_fixer
import openai
from agent.config import store_info, customer_service_task

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# set up llm
LLM_CLIENT = initialize_async_llm_client()
LLM_MODEL_ID = os.environ.get('LLM_MODEL_ID', '')

SYSTEM_PROMPT = '''\
Your job is to generate a response to the customer from the Assistant.
The assistant is a helpful, kind customer service agent for this store.
Use the conversation and previous tool calls (if provided) to generate a response.

## Store information
{store_info}

## Customer Service Task
{customer_service_task}

## Response Tone and Style
* Make sure your response is extremely human-like. This is a casual conversation, not a formal business interaction.
* Never greet the customer unless they initiate a greeting without a request. Get straight to what they want instead of using pleasantries.

## Conversation History

In the conversation, the customer will be able to both hear you and visually see the output from the last tool on the app screen. \
This should impact how you respond to the customer. 

Here is the conversation so far:

{conversation}

## Output Format
You must return a perfectly formatted JSON object which can be serialized with the following keys:
- 'reason': a string explaining what you will talk about in your response.
- 'response': the response to the customer from the assistant.

The 'reason' string should follow a logical step by step pattern like below:

"To address the customer's inquiry about <customer inquiry> \
The information provided by the tools tells me <analysis of the tool outputs>.
The customer is able to see <last tool call information>.
The tool outputs are missing <missing information> to answer the customer's inquiry.
Based on the tool outputs, I will give the customer a factually grounded response which says <response to the customer>"

In the 'response' key, you should always spell numbers out if you relaying a number to the customer. For example \
you should not say "this costs $4.95" but instead "this costs four dollars and ninety five cents".

If your response contains information contained in the visual which is available to the customer, \
you should simply reference the screen "below" instead of repeating the information.

Here are some examples of good and bad response patterns when a tool is visible to the customer:
* Last tool output visible to customer: <A list of products with prices>
    * Bad: "We have four products available. Product a with costs X dollars. Product b which costs Y dollars ..."
    * Good: "Check out these options and let me know what you think"
* Last tool output visible to customer: <An updated cart summary>
    * Bad: "I have added product A to your cart. Your updated cart totals is X dollars and Y cents."
    * Good: "Alright your cart has been updated. Does this look good to you?"
* Last tool output visible to customer: <Order confirmation>
    * Bad: "Thank you for you order. Your order confirmation number is one two three four ..."
    * Good: "Thank you for your order! You can view your order details in the link below."

## Rules
* Your response must be VERY concise. Do not use filler language. More than one sentence is discouraged.
* Do not reference "the screen" in your response. It is implicit that the customer can see the screen.
* You are strictly forbidden from assuming any information about the store that has not been provided to you. \
Do not use simple assumptions about products, services, or variations available at the store \
no matter how simple they might be. So, when you stating your "reason", make sure you cite the tool outputs \
if you are providing details about the store, products, orders, cart, etc.
* If a customer asks a question you cannot answer based on the tool outputs, you should tell them that you do not know.
* Relaying any information to the customer which is not present in the conversational context or previous tool calls \
will result in a penalty.
'''

SYSTEM_PROMPT = SYSTEM_PROMPT.replace('{store_info}', store_info).replace('{customer_service_task}', customer_service_task)

TOOL_CACHE_PROMPT = '''
assistant:
### Tools Used Before Responding to Customer

{tool_output_cache}
'''


class CustomerResponse(Node):
    def __init__(self, name, attributes):
        super().__init__(name, attributes)
        self.llm_client = LLM_CLIENT
        self.llm_model_id = LLM_MODEL_ID

    @observability_decorator('CustomerResponse')
    async def process(self, messages: list, input: dict):
        try:
            logger.info(f"CustomerResponse processing messages: {messages}")

            # make a single system prompt which has the conversation if needed
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
            yield {
                'node': self.id,
                'reason' : customer_response_output['reason'],
                'output': customer_response_output['response'],
                'memory': input.get('memory', {})
            }
            logger.info("CustomerResponse finished processing")
        except Exception as e:
            logger.exception(f"An error occurred in CustomerResponse")
            raise e

    async def get_successors(self, result: dict):
        return []
