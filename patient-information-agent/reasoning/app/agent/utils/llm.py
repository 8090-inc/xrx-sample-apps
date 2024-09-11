import os
from langsmith.wrappers import wrap_openai
from functools import wraps, partial
from dotenv import load_dotenv
from langfuse.decorators import observe as langfuse_observe
from langsmith import traceable as langsmith_traceable

load_dotenv()
observability_library = os.getenv("LLM_OBSERVABILITY_LIBRARY", '').lower()
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')

def initialize_llm_client():
    logging.info("Initializing LLM client.")
    LLM_API_KEY = os.environ.get('LLM_API_KEY', '')
    LLM_BASE_URL = os.environ.get('LLM_BASE_URL', '')
    LLM_MODEL_ID = os.environ.get('LLM_MODEL_ID', '')
    logging.info("LLM API KEY : ***************")
    logging.info(f"LLM Base URL: {LLM_BASE_URL}")
    logging.info(f"LLM Model ID: {LLM_MODEL_ID}")

    if not LLM_API_KEY or not LLM_BASE_URL or not LLM_MODEL_ID:
        raise EnvironmentError("LLM_API_KEY or LLM_BASE_URL or LLM_MODEL_ID is not set in the environment variables.")

    if observability_library in ["langfuse"]:
        from langfuse.openai import openai
        llm_client = openai.OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
    else:
        from openai import OpenAI
        llm_client = wrap_openai(OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL))

    return llm_client

def observability_decorator(name= None):
    if observability_library in ["langfuse"]:
        decorator = partial(langfuse_observe, name=name) if name else langfuse_observe
    else:
        decorator = partial(langsmith_traceable, name=name) if name else langsmith_traceable

    def wrapper(func):
        @wraps(func)
        def wrapped_func(*args, **kwargs):
            return decorator()(func)(*args, **kwargs)
        return wrapped_func
    return wrapper