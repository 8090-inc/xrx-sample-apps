import requests
import json
import uuid
from termcolor import colored
from rich import print as rprint

# Define the URL
url = "http://127.0.0.1:8003/run-reasoning-agent"

# Define the headers
headers = {
    "Content-Type": "application/json",
    "Accept": "text/event-stream",
}

# Single turn test
body = {
    'session': {
        'id': 1234,
    },
    'messages': [
        {
            "role": "user",
            "content": "i wanna order a pizza"
        },
    ]
}

# Send the POST request
response = requests.post(url, headers=headers, data=json.dumps(body), stream=True)

try:
    # Stream the response
    for line in response.iter_lines(decode_unicode=True):
        if line.startswith('data: '):
            rprint('\n\n-----------------')
            data = json.loads(line[6:])
            rprint(data)
except KeyboardInterrupt:
    print("\nScript interrupted by user")
finally:
    response.close()
    print("Connection closed")
