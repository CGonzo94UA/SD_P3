# syntax=docker/dockerfile:1
FROM python:alpine

RUN pip install kafka-python
RUN pip install pycryptodomex

COPY AA_NPC.py AA_NPC.py
COPY aesEncryptDecrypt.py aesEncryptDecrypt.py
COPY NPCParameters.json NPCParameters.json
