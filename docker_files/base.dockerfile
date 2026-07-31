FROM python:3.13-slim

WORKDIR /opt/src

COPY requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt
