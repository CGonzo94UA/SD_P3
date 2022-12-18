# syntax=docker/dockerfile:1
FROM python:alpine

COPY AA_Registry.py AA_Registry.py
COPY RegistryParameters.json RegistryParameters.json

RUN pip install flask
RUN pip install mysql-connector-python
