FROM python:3.10-slim

WORKDIR /app

COPY reasoning/requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY reasoning/app .
COPY xrx-core/agent_framework /app/agent_framework

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]
