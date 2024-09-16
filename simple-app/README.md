# Simple Reasoning Agent

## Overview

This project features a simple reasoning app designed to demonstrate basic logical reasoning capabilities. The agent is built to autonomously process text input and provide responses based on a predefined set of rules or knowledge base. This agent serves as a foundation for more complex reasoning systems and can be easily modified for various tasks.

* **Table of Contents:**
  * Features
  * Getting Started
  * How To Run
  * Project Structure
  * API Usage
  * Contributing

## Features
This app serves as an example of how to implement specific tools within the xRx framework. It showcases two custom tools: a weather tool for retrieving forecasts and a stock tool for obtaining information about stocks. The application leverages a language model for natural language processing and response generation, ensuring smooth interaction with users. Built on FastAPI, it offers robust and efficient web server performance. Additionally, the app includes observability and logging features, facilitating easy monitoring and debugging of the system.

## Getting Started

### Prerequisites

* We assume you have already cloned the repository, as explained in the general README. For the sake of clarity, here's the command again:
   ```
   git clone --recursive https://github.com/8090-inc/xrx-sample-apps.git
   ```

* If the submodule was not installed, or you want to update it, use the following command:
   ```
   git submodule update --init --recursive
   ```

* Install `Docker`, `Python3`, and `Pip3` with [homebrew](https://formulae.brew.sh/) on macOS or `apt-get update` on Debian/Ubuntu based Linux systems:

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
   docker run -p 8003:8003 --env-file .env simple-reasoning-agent:latest
   ```

The agent will be accessible at `http://localhost:8003`.


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
  uvicorn main:app --host 127.0.0.1 --port 8003 --reload
  ```

The agent will now be running at `http://localhost:8003` (or the port specified in your `.env` file).

## Project Structure

- `app/`: Contains the main application code
  - `agent/`: Agent logic
    - `executor.py`: Main agent execution logic
    - `tools/`: Folder containing agent tools
      - `generic_tools.py`: Generic tools for the agent
  - `__init__.py`: Initializes the app module
  - `main.py`: FastAPI application setup and endpoint definition
- `test/`: Contains test files
- `xrx-core/`: Core xRx framework (submodule)
- `Dockerfile`: Docker configuration for containerization
- `requirements.txt`: Python dependencies
- `docker-compose.yaml`: Docker Compose configuration file
- `env-example.txt`: Example environment variables file
- `README.md`: Project documentation

## API Usage

The agent exposes a single endpoint using FastAPI:

- `POST /run-reasoning-agent`: Submit a query to the reasoning agent and receive streaming responses.

Example request using `curl`:

```bash
curl -X POST http://localhost:8003/run-reasoning-agent \
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

url = "http://localhost:8003/run-reasoning-agent"
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


## Project Structure

- `app/`: Contains the main application code
  - `agent/`: Agent logic
    - `executor.py`: Main agent execution logic
    - `tools/`: Folder containing agent tools
      - `generic_tools.py`: Generic tools for the agent
  - `__init__.py`: Initializes the app module
  - `main.py`: FastAPI application setup and endpoint definition
- `test/`: Contains test files
- `xrx-core/`: Core xRx framework (submodule)
- `Dockerfile`: Docker configuration for containerization
- `requirements.txt`: Python dependencies
- `docker-compose.yaml`: Docker Compose configuration file
- `env-example.txt`: Example environment variables file
- `README.md`: Project documentation

## Contributing

Contributions to improve the Simple App are welcome. Please follow these steps:

1. Open a new issue on GitHub describing the proposed change or improvement
2. Fork the repository
3. Create a new branch for your feature
4. Commit your changes
5. Push to your branch
6. Create a pull request, referencing the issue you created

> **Note:** pull requests not backed by published issues will not be considered. This process ensures that all contributions are discussed and aligned with the project's goals before implementation.
