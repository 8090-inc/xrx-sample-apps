from fastapi import FastAPI, Request, HTTPException, Path
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from agent.executor import run_agent

import redis
import logging
import os
import uuid

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Initialize Redis client
redis_host = os.getenv('REDIS_HOST', 'localhost')
redis_client = redis.asyncio.Redis(host=redis_host, port=6379, db=0)

app = FastAPI()

class Message(BaseModel):
    role: str
    content: str

class AgentRequest(BaseModel):
    messages: List[Message] = Field(..., description="List of messages in the conversation")
    session: Dict[str, Any] = Field(default_factory=dict, description="Session information for the conversation")
    action: Optional[Dict[str, Any]] = Field({}, description="Optional action to be performed by the agent")

class CancelResponse(BaseModel):
    detail: str

async def stream_run_agent(body):
    try:

        # start the stream async generator
        logger.info("Starting run_agent")
        task_id = body.get("task_id")
        async for result in run_agent(body):

            # otherwise yield the result out
            logger.info(f"Yielding result: {result}")
            yield f"data: {result}\n\n"

            # stop execution if there is an error
            if 'error' in result:
                return
        logger.info("Finished run_agent")
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        yield f"data: An error occurred: {str(e)}\n\n"
        return

@app.post("/run-reasoning-agent", response_class=StreamingResponse)
async def execute_agent(request: Request, agent_request: AgentRequest):
    """
    Execute the reasoning agent and stream the results.

    This endpoint starts a new task for the reasoning agent and returns
    a streaming response with the agent's output.

    The task ID is returned in the 'X-Task-ID' header of the response.

    Args:
        request (Request): The request object containing headers and client information.
        agent_request (AgentRequest): The input for the reasoning agent, including messages, session information, and an optional action.

    Returns:
        StreamingResponse: A streaming response containing the agent's output.

    Raises:
        HTTPException: If an error occurs during processing.
    """
    try:
        body = agent_request.model_dump()
        logger.info(f"Received request body: {body}")
        logger.info(f"Request headers: {request.headers}")
        logger.info(f"Request client: {request.client}")

        # create the task id
        task_id = str(uuid.uuid4())
        logger.info(f"Created task with task ID: {task_id}")
        body['task_id'] = task_id

        # store the task id in redis
        await redis_client.set(task_id, 'running')
        logger.info(f"Stored task ID {task_id} in Redis with status 'running'")

        # return the task id in the header as well
        headers = {"X-Task-ID": task_id}

        return StreamingResponse(stream_run_agent(body), media_type="text/event-stream", headers=headers)
    except HTTPException as e:
        logger.error(f"HTTPException occurred: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"An error occurred while processing the request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cancel-reasoning-agent/{task_id}", response_model=CancelResponse)
async def cancel_agent(
    task_id: str = Path(..., description="The ID of the task to cancel")
):
    """
    Cancel a running reasoning agent task.

    This endpoint attempts to cancel a task identified by the given task_id.
    It sets the task status to 'cancelled' in Redis.

    Args:
        task_id (str): The ID of the task to cancel.

    Returns:
        CancelResponse: A response indicating the result of the cancellation attempt.

    Raises:
        HTTPException: If an error occurs during the cancellation process.
    """
    try:
        # Set task status to cancelled in Redis
        await redis_client.set('task-' + task_id, 'cancelled')
        logger.info(f"Task {task_id} set to cancelled")
        return JSONResponse(content={"detail": f"Task {task_id} cancelled"}, status_code=200)
    except Exception as e:
        logger.error(f"An error occurred while cancelling the task: {str(e)}")
        return JSONResponse(content={"detail": f"An error occurred: {str(e)}"}, status_code=500)
