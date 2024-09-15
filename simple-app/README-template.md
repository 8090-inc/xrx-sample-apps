# Template Reasoning Agent

## Overview

This project features a blank reasoning agent designed to be a building block for logical reasoning capabilities in xRx. This agent serves as a starting point for developers to implement their own custom reasoning systems within the xRx framework.

## Getting Started

### Prerequisites

Install Docker, Python3, and Pip3 with homebrew on macOS or apt-get update on Debian/Ubuntu based Linux systems:

```bash
brew cask install docker
brew install python@3.10
```

## How To Run

### Using Docker

1. Build the Docker image:
   ```bash
   docker build -t template-reasoning-agent:latest .
   ```

2. Run the container:
   ```bash
   docker run -p 8093:8093 --env-file .env template-reasoning-agent:latest
   ```

The agent will be accessible at http://localhost:8093.

### Locally without Docker

1. Set up the Python virtual environment:
   ```bash
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

The agent will now be running at http://localhost:8093


## Implementing Your Reasoning Agent

The main logic for your reasoning agent should be implemented in the `single_turn_agent` function in the file `app/agent/executor.py`. Here's the default implementation:

```python
def single_turn_agent(messages: List[dict]) -> str:
    # REASONING CODE GOES HERE
    message = {
        "role": "assistant",
        "content": "I'm a reasoning agent. Please implement me!"
    }
    out = {
        "messages": [message],
        "node": "CustomerResponse",
        "output": message['content'],
    }
    return out
```

Replace the placeholder code with your own reasoning logic. You can use external libraries, APIs, or implement custom algorithms as needed.

## Testing Your Reasoning Agent

To test your reasoning agent:

1. Start the FastAPI server:
   ```bash
   cd app
   uvicorn main:app --port 8093 --reload
   ```

2. In another terminal, run the interactive CLI testing script:
   ```bash
   cd test
   python test_agent.py
   ```

## API Usage

The agent exposes a single endpoint using FastAPI:

- POST `/run-reasoning-agent`: Submit a query to the reasoning agent and receive streaming responses.

Example request using curl:

```bash
curl -X POST http://localhost:8093/run-reasoning-agent \
     -H "Content-Type: application/json" \
     -H "Accept: text/event-stream" \
     -d '{
         "session": {
             "id": "1234567890"
         },
         "messages": [
             {"role": "user", "content": "Hi what is your name?"}
         ]
     }'
```

Example response (streaming):

```json
{
    "messages": [
        {"role": "assistant", "content": "I'm a reasoning agent. Please implement me!"}
    ],
    "session": {"id": "1234567890"},
    "node": "CustomerResponse",
    "output": "I'm a reasoning agent. Please implement me!"
}
```

## Environment Configuration

Create a `.env` file in the root directory of your project. Use the provided `env-example.txt` as a template. Here's a minimal example:

```
# LLM Configuration
LLM_API_KEY="your_api_key_here"
LLM_BASE_URL="https://api.groq.com/openai/v1"
LLM_MODEL_ID="llama3-70b-8192"

# Agent Configuration
INITIAL_RESPONSE="Hello! How can I help you?"

# LLM Observability
LLM_OBSERVABILITY_LIBRARY="none"

# Redis Configuration
REDIS_HOST="localhost"
```

## Project Structure

- `app/`: Contains the main application code
  - `main.py`: FastAPI application setup and endpoint definition
  - `agent/`: Core agent logic
  - `executor.py`: Main agent execution logic
  - `utils/`: Utility functions and LLM integration
- `test/`: Contains testing scripts
- `requirements.txt`: Python dependencies
- `Dockerfile`: Docker configuration for containerization
- `docker-compose.yaml`: Docker Compose configuration for the xRx system

## Deploying the xRx System

To deploy the entire xRx system with your custom reasoning agent:

1. Ensure your `.env` file is properly configured.
2. Run the following command in the project root directory:

```bash
docker compose up --build
```

This will build and start all the necessary containers for the xRx system, including your custom reasoning agent.

## Contributing

Contributions to improve the Template Reasoning Agent are welcome. Please follow these steps:

1. Fork the repository
2. Create a new branch for your feature
3. Commit your changes
4. Push to your branch
5. Create a pull request

## License

[Insert appropriate license information here]