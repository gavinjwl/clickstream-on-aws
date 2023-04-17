FROM python:3.9-slim-buster

WORKDIR /app

COPY requirements.txt  .
RUN  pip3 install --no-cache-dir --upgrade -r requirements.txt --target .

# Copy function code
COPY env.py .
COPY kinesis_producer.py .
COPY models.py .
COPY routers ./routers
COPY server.py .

CMD ["python", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
