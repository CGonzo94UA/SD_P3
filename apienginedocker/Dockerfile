# syntax=docker/dockerfile:1
FROM python:alpine

COPY API_Engine.py API_Engine.py
COPY APIEngineParameters.json APIEngineParameters.json

RUN pip install flask
RUN pip install mysql-connector-python
RUN pip install flask_cors

CMD ["python", "API_Engine.py"]
