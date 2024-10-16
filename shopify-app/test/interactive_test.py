import unittest
import requests
import json
import uuid
from rich import print as rprint
from termcolor import colored
from rich import print as rprint
import pdb

# Define the URL
url = "http://127.0.0.1:8003/run-reasoning-agent"

headers = {
    "Content-Type": "application/json",
    "Accept": "text/event-stream",
}

def send_messages(messages, user_input, session):
    messages.append({"role": "user", "content": user_input})
    body = {
        'session': session,
        'messages': messages,
    }
    response = requests.post(
        url,
        headers=headers,
        data=json.dumps(body),
        stream=True
    )
    for line in response.iter_lines(decode_unicode=True):
        if line.startswith('data: '):
            data = json.loads(line[6:])
            print('- - - '*10)
            print(colored("Graph Agent Output:", 'yellow'))

            # DEBUG for state machine work; 
            # TODO(mprast): perhaps add functionality to trim verbose session output?
            if isinstance(data, str) or 'error' in data:
                rprint(data)
            else:
                data_copy = data.copy()
                session_copy = data_copy['session'].copy()
                data_copy['session'] = session_copy

                # get rid of session, get rid of messages, output at bottom, 
                # different color

                if 'session' in data_copy:
                    if 'stateMachine' in data_copy['session']:
                        del data_copy['session']
                        del data_copy['messages']
                        data_copy['__output'] = data_copy['output']
                        del data_copy['output']
                        
                        if data_copy['node'] == 'CustomerResponse':
                            print(colored("Agent Response: " + data_copy['__output'], 'cyan'))

                        #data_copy['session']['stateMachine'] = "<lengthy state machine info redacted>"

                rprint(data_copy)
    if 'error' in data:
        print(colored("Error:", 'red'), data)
        return None, None, None
    new_messages = data['messages']
    new_session = data['session']
    messages = messages + new_messages
    response.close()
    return new_messages[-1]['content'], messages, new_session

def main():
    print("Interactive Shopify Agent Test. Type 'quit' to exit.")
    messages = []
    session = {
        'guid': str(uuid.uuid4()),
    }
    while True:
        print('========'*10)
        user_input = input(colored("Customer: ", 'blue'))
        if user_input.lower() == 'quit':
            break
        response, messages, session = send_messages(messages, user_input, session)

if __name__ == "__main__":
    main()
