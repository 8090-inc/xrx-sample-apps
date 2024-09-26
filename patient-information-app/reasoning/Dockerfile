FROM python:3.10-slim

WORKDIR /app

COPY xrx-core/xrx_agent_framework /xrx-core/xrx_agent_framework

COPY reasoning/requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY reasoning/app .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]