FROM python:3.10-slim

WORKDIR /agent

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY ./app ./

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]
