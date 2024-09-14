import unittest
import requests
import json
import uuid
from rich import print as rprint
from termcolor import colored

class TestShopifyAgent(unittest.TestCase):
   
    URL = "http://127.0.0.1:8003/run-reasoning-agent"
    ITERATIONS = 5

    HEADERS = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }

    def setUp(self):
        self.session = { 'guid': str(uuid.uuid4())}
        self.test_messages = [
            "I want a pizza.",
            "hello!",
            "I want a large pizza.",
            "How much is a medium pizza?",
            "Whats on the menu?"
        ]

    def test_single_turn_agent_responses(self):
        for message in self.test_messages:
            with self.subTest(message=message):
                response = self.send_request(message, [])
                self.process_response(response, message, [])
                

    def test_multiple_single_turn_iterations(self):      
        for message in self.test_messages:
            with self.subTest(message=message):
                for i in range(self.ITERATIONS):
                    with self.subTest(iteration=i+1):                       
                        rprint(f"\n[Iteration {i+1}]")
                        response = self.send_request(message, [])
                        self.process_response(response, message, [])

    def test_multi_turn_conversations(self):
        conversations = [
            [
                "How much is a medium pizza?",
                "Ok I'll take one of those please",
                "Nope that is all I need"
            ],
            [
                "What's on the menu?",
                "What size of pizzas are there?",
                "How much is the large?"
            ]
        ]
        
        for conversation in conversations:
            conversation_history = []
            for message in conversation:
                with self.subTest(message=message):
                    response = self.send_request(message, conversation_history)
                    self.process_response(response, message, conversation_history)

    def send_request(self, message, conversation_history):
        body = {
            'session': self.session,
            'messages': conversation_history + [{"role": "user", "content": message}]
        }
        rprint(f"\n[Sending message: {message} with conversation history: {conversation_history}]")
        return requests.post(self.URL, headers=self.HEADERS, json=body, stream=True)

    def process_response(self, response, message, conversation_history):
        self.assertEqual(response.status_code, 200)
        full_response = []
        for line in response.iter_lines(decode_unicode=True):
            rprint(f"\tReceived Response: {line}")
            if line.startswith('data: '):
                try:
                    data = json.loads(line[6:])
                    if isinstance(data, dict) and 'output' in data:
                        output = data['output']
                        full_response.append(output)
                    elif isinstance(data, str):
                        full_response.append(data)
                except json.JSONDecodeError:
                    rprint(f"\tFailed to parse JSON: {line[6:]}")

        rprint(f"\nFull Response: {full_response}")
        self.assertTrue(full_response, "Full response is empty")        
        conversation_history.append({"role": "user", "content": message})
        conversation_history.append({"role": "assistant", "content": ' '.join(str(response) for response in full_response)})

if __name__ == '__main__':
    unittest.main()