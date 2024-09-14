# Simple Reasoning Agent

## Overview

This project features a simple reasoning agent designed to demonstrate basic logical reasoning capabilities. The agent is built to autonomously process text input and provide responses based on a predefined set of rules or knowledge base. This agent serves as a foundation for more complex reasoning systems and can be easily modified for various tasks.

## Getting Started

### Prerequisites

Install `Docker`, `Python3`, and `Pip3` with [homebrew](https://formulae.brew.sh/) on macOS or `apt-get update` on Debian/Ubuntu based Linux systems:

```bash
brew cask install docker
brew install python@3.10
```

### Environment Variables

The following environment variables are required:

- `LLM_API_KEY`: Your API key for the language model service (e.g., OpenAI, Groq)
- `LLM_BASE_URL`: The base URL for the language model API
- `LLM_MODEL_ID`: The ID of the language model to use

Create a `.env` file in the root directory of your project. Use the provided `env-example.txt` as a template. Here's a minimal example:

```
LLM_API_KEY=your_api_key_here
LLM_BASE_URL="https://api.groq.com/openai/v1"
LLM_MODEL_ID="llama3-70b-8192"
```

## How To Run

### Using Docker

1. Build the Docker image:
   ```bash
   docker build -t simple-reasoning-agent:latest .
   ```

2. Run the container:
   ```bash
   docker run -p 8093:8093 --env-file .env simple-reasoning-agent:latest
   ```

The agent will be accessible at `http://localhost:8093`.


### Locally without Docker

1. Set up the Python virtual environment:
  ```
  python3 -m venv venv
  source venv/bin/activate
  ```

2. Install requirements:
  ```bash
  pip install -r requirements.txt
  ```
3. Start a local redis cluster
  ```bash
  redis-server --port 6379
  ```

4. Run the application:
  ```bash
  cd app
  uvicorn main:app --host 127.0.0.1 --port 8093 --reload
  ```

The agent will now be running at `http://localhost:8093` (or the port specified in your `.env` file).


## API Usage

The agent exposes a single endpoint using FastAPI:

- `POST /run-reasoning-agent`: Submit a query to the reasoning agent and receive streaming responses.

Example request using `curl`:

```bash
curl -X POST http://localhost:8093/run-reasoning-agent \
     -H "Content-Type: application/json" \
     -H "Accept: text/event-stream" \
     -d '{
           "session": {
               "id": "1234567890"
           },
           "messages": [
               {"role": "user", "content": "What is the weather like in Paris?"}
           ]
         }'
```

Example request using Python's `requests` library with streaming:

```python
import requests
import json

url = "http://localhost:8093/run-reasoning-agent"
headers = {
    "Content-Type": "application/json",
    "Accept": "text/event-stream",
}
payload = {
    "session": {"id": "1234567890"},
    "messages": [{"role": "user", "content": "What is the weather like in Paris?"}]
}

response = requests.post(url, headers=headers, data=json.dumps(payload), stream=True)

for line in response.iter_lines(decode_unicode=True):
    if line.startswith('data: '):
        data = json.loads(line[6:])
        print(data)
```

Example response (streaming):

```json
{
  "messages": [
    {"role": "assistant", "content": "The weather in Paris is currently sunny with a temperature of 20°C."}
  ],
  "session": {"id": "1234567890"}
}
```

To view the interactive API documentation, visit `http://localhost:8093/docs` in your web browser after starting the server.
