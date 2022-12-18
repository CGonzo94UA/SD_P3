# syntax=docker/dockerfile:1
FROM python:alpine

RUN pip install kafka-python
RUN pip install pycryptodomex
RUN pip install requests

COPY AA_Player.py AA_Player.py
COPY aesEncryptDecrypt.py aesEncryptDecrypt.py
COPY AESPassword.json AESPassword.json
COPY PlayerParameters.json PlayerParameters.json
