from typing import List
import json
import os
import logging
import redis

from agent_framework import initialize_llm_client, observability_decorator
from .context_manager import set_session, session_var

# set up the redis client
redis_host = os.getenv('REDIS_HOST', 'localhost')
redis_client = redis.asyncio.Redis(host=redis_host, port=6379, db=0)

# set up the LLM
client = initialize_llm_client()
MODEL = os.environ['LLM_MODEL_ID']

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')

SYSTEM_PROMPT = """You are a highly trained medical assistant. You are responsible for retrieving information from a patient before a doctor visit.

## Style and Tone
* You should remain friendly and concise.
* Roll with the punches while staying on task of getting your required information.
* Your response will be said out loud as audio to the patient, so make sure your response will sound natural when it is spoken.
* You should sound like a normal person. Do not sound robotic at all.

## Necessary information

You are in charge of retrieving the following information from the patient:

* "name"
    * Must contain both a first and last name
* "date-of-birth"
    * Must be in the format "Month Day, Year"
* "allergies"
    * Must be in the format of a comma separated list
    * Examples: "Peanuts, Shellfish", "None"
* "current-medications"
    * Must be in the format of a comma separated list
    * Examples: "Aspirin, Ibuprofen", "None"
* "reason-for-visit"
    * Must be in the format of a comma separated list
    * Examples: "headache, fever", "sore throat, cough, runny nose", "knee pain", "general checkup"

## Output format

Your response must be perfectly formatted JSON with the following structure

{
    "information-received": {
        "key": "value",
    },
    "response": "your response to the customer"
}

The "key" should be one of the keys in the "necessary information" section above if and only if the COMPLETE information is received from the patient.

Here is an example of what your output should look like

[start example 1]
Assistant: Hello! I would like to get some information from you to start your appointment. Ready to begin?
User: Sounds good
Assistant:
{
    "information-received": {},
    "response": "Can you please confirm your first and last name"
}
User: Yes my name is John Doe
Assistant:
{
    "information-received": {
        "name": "John Doe"
    }
    "response": "Thanks John! When were you born?"
}
User: I was born on march first
Assistant:
{
    "response": "And what year was that?",
    "information-received": {}
}
User: 1997
Assistant:
{
    "response": "And what year was that?",
    "information-received": {"date-of-birth": "March 1st, 1997"}
}

## Rules
* Ask feedback questions if you do not understand what the person was saying
* Always speak in a human-like manner. Your goal is to sound as little like a robotic voice as possible.
* Do not ask people for specific formats of information. Ask them like a normal person would.
"""

@observability_decorator(name="run_agent")
async def run_agent(input_dict: dict):
    try:
        logging.info("Starting Agent Executor.")

        messages = input_dict['messages']
        session = input_dict['session']
        task_id = input_dict.get('task_id', '')

        # Use the context manager to set the session
        with set_session(session):
            async for response in single_turn_agent(messages, task_id):
                response['session'] = session_var.get()
                logging.info(f"Agent Output: {json.dumps(response)}")
                yield json.dumps(response)

    except Exception as e:
        logging.exception(f"An error occurred: {e}")

async def single_turn_agent(messages: List[dict], task_id: str):

    # set up the base messages
    system_prompt = {
        "role": "system",
        "content": SYSTEM_PROMPT
    }
    first_assistant_message = {
        "role": "assistant",
        "content": "Hello! I would like to get some information from you to start your appointment. Ready to begin?"
    }
    messages.insert(0, system_prompt)
    messages.insert(1, first_assistant_message)

    # call the language model
    response = client.chat.completions.create(
        model=os.environ['LLM_MODEL_ID'],
        messages=messages,
        max_tokens=4096,
        response_format={
            "type": "json_object"
        }
    )

    # save the message
    response_message = response.choices[0].message.content
    messages.append(
        {
            "role": "assistant",
            "content": response_message
        }
    )

    # parse the response
    response_message_dict = json.loads(response_message)
    customer_response = response_message_dict['response']
    information_received = response_message_dict['information-received']

    # get old session information
    session_data = session_var.get()

    # add new information to the session
    information_received_schema = {
        "name": "",
        "date-of-birth": "",
        "allergies": "",
        "current-medications": "",
        "reason-for-visit": ""
    }
    if 'information-received' in session_data.keys():
        logging.info(f"Old information received: {session_data['information-received']}")
        old_information_received = json.loads(session_data['information-received'])
        information_received = {**old_information_received, **information_received}
    else:
        logging.info(f"No old information received")
        information_received = information_received_schema
    information_received = json.dumps(information_received)
    logging.info(f"Information received: {information_received}")
    
    # store the information received in the session
    session_data['information-received'] = information_received
    session_var.set(session_data)

    # check if the task has been canceled
    redis_status = await redis_client.get('task-' + task_id)
    logging.info(f"Task {task_id} has status {redis_status}")
    if redis_status == b'cancelled':
        return

    # now yield the widget information
    widget_output = {
        'type': 'patient-information',
        'details': information_received,
    }
    out = {
        "messages": [messages[-1]],
        "node": "Widget",
        "output": widget_output,
    }
    yield out

    # use the "node" and "output" fields to ensure a response is sent to the front end through the xrx orchestrator
    out = {
        "messages": [messages[-1]],
        "node": "CustomerResponse",
        "output": customer_response,
    }
    yield out
