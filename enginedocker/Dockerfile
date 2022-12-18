# syntax=docker/dockerfile:1
FROM python:alpine

RUN pip install kafka-python
RUN pip install mysql-connector-python
RUN pip install pycryptodomex
RUN pip install requests

COPY AA_Engine.py AA_Engine.py
COPY EngineParameters.json EngineParameters.json
COPY aesEncryptDecrypt.py aesEncryptDecrypt.py
COPY AESPassword.json AESPassword.json
COPY Cities.txt Cities.txt
