import requests
import json
import uuid
import time
from termcolor import colored
from rich import print as rprint
import threading

# Define the URLs
run_url = "http://127.0.0.1:8003/run-reasoning-agent"
cancel_url = "http://127.0.0.1:8003/cancel-reasoning-agent/"

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
            "content": "how much is a medium pizza?"
        },
    ]
}

def cancel_request(task_id):
    time.sleep(2)
    rprint(f"Canceling request with task ID: {task_id}")
    cancel_response = requests.post(cancel_url + task_id)
    rprint(f"Cancel response: {cancel_response.json()}")

# Send the POST request
response = requests.post(run_url, headers=headers, data=json.dumps(body), stream=True)

try:
    # Get the task ID from the response headers
    task_id = response.headers.get('X-Task-ID')
    if task_id:
        # Start a thread to cancel the request after 2 seconds
        threading.Thread(target=cancel_request, args=(task_id,)).start()

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
