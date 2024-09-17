# Patient Information App

## Overview

This project features a reasoning agent designed to gather patient information before a doctor's visit. The agent interacts with patients through a conversational interface, collecting essential details such as name, date of birth, allergies, current medications, and reason for visit. This agent is built on top of the xRx framework, providing a seamless experience for patient intake.

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

## How To Run

### Using Docker

1. Build the Docker image:
   ```bash
   docker build -t patient-information-agent:latest .
   ```

2. Run the container:
   ```bash
   docker run -p 8003:8003 --env-file .env patient-information-agent:latest
   ```

The agent will be accessible at http://localhost:8003.

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
   uvicorn main:app --host 127.0.0.1 --port 8003 --reload
   ```

The agent will now be running at http://localhost:8003

## Project Structure

- `reasoning/`: Contains the main application code
  - `app/`: backend application folder
    - `agent/`: agent logic
      - `context_manager.py`: Manages session context
      - `executor.py`: Main agent execution logic
    - `__init__.py`: Initializes the app module
    - `main.py`: FastAPI application setup and endpoint definition
  - `Dockerfile`: Docker configuration for containerization
  - `requirements.txt`: Python dependencies
- `nextjs-client/`: Next.js frontend for the patient intake application
- `test/`: Contains test files
- `xrx-core/`: Core xRx framework (submodule)
- `docker-compose.yaml`: Docker Compose configuration file
- `env-example.txt`: Example environment variables file
- `README.md`: Project documentation

## API Usage

The agent exposes a single endpoint using FastAPI:

- **POST** `/run-reasoning-agent`: Submit a query to the reasoning agent and receive streaming responses.

### Example request using curl

```bash
curl -X POST http://localhost:8003/run-reasoning-agent \
     -H "Content-Type: application/json" \
     -H "Accept: text/event-stream" \
     -d '{
         "session": {
             "id": "1234567890"
         },
         "messages": [
             {"role": "user", "content": "Hi, I'm here for my appointment."}
         ]
     }
```

### Example request using Python's requests library with streaming

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
    "messages": [{"role": "user", "content": "Hi, I'm here for my appointment."}]
}

response = requests.post(url, headers=headers, data=json.dumps(payload), stream=True)

for line in response.iter_lines(decode_unicode=True):
    if line.startswith('data: '):
        data = json.loads(line[6:])
        print(data)
```

### Example response (streaming)

```json
{
    "messages": [
        {"role": "assistant", "content": "Hello! Welcome to our clinic. I'd be happy to help you check in for your appointment. Can you please tell me your full name?"}
    ],
    "session": {"id": "1234567890"},
    "node": "CustomerResponse",
    "output": "Hello! Welcome to our clinic. I'd be happy to help you check in for your appointment. Can you please tell me your full name?"
}
```

To view the interactive API documentation, visit `http://localhost:8093/docs` in your web browser after starting the server.

## Environment Variables

Ensure you have the following environment variables set in your `.env` file:

- `LLM_API_KEY`: API key for the language model service
- `LLM_BASE_URL`: Base URL for the language model API
- `LLM_MODEL_ID`: ID of the language model to use
- `REDIS_HOST`: Hostname for the Redis server (default: "localhost")

## Testing

To run tests, use the following command from the project root:

```bash
python -m unittest discover test
```

## Frontend

The project includes a Next.js frontend in the `nextjs-client/` directory. To run the frontend:

1. Navigate to the `nextjs-client/` directory
2. Install dependencies: `npm install`
3. Run the development server: `npm run dev`

The frontend will be available at http://localhost:3000.

## Contributing

Contributions to improve the Patient Information Agent are welcome. Please follow these steps:

1. Open a new issue on GitHub describing the proposed change or improvement
2. Fork the repository
3. Create a new branch for your feature
4. Commit your changes
5. Push to your branch
6. Create a pull request, referencing the issue you created

> **Note:** pull requests not backed by published issues will not be considered. This process ensures that all contributions are discussed and aligned with the project's goals before implementation.