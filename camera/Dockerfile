# syntax=docker/dockerfile:1

FROM debian:10

WORKDIR /speed-trap

RUN apt-get update && \
    apt-get install -y python3-pip python3-opencv v4l-utils

COPY . /speed-trap

RUN pip3 install -r requirements.txt


CMD [ "python3", "main.py"]