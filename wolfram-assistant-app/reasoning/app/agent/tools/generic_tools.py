import requests
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')


def get_wolfram_response(question):
    """
    Retrieves a wolfram response for a given question.
    """
    app_id = os.getenv("WOLFRAM_API_ID")
    base_url = os.getenv("WOLFRAM_BASE_URL")
    params = {
        'i': question,
        'appid': app_id
    }
    logging.info(f"PARAMS: {params}")
    response = requests.get(base_url, params=params)
    logging.info(f"RESPONSE: {response}")
    
    if response.status_code == 200:
        return response.text
    else:
        return "Sorry, I couldn't find an answer to your question."
