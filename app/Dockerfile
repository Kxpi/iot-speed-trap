# syntax=docker/dockerfile:1

FROM debian:10

WORKDIR /api-handler

RUN apt-get update && \
    apt-get install -y python3-pip

COPY . /api-handler

RUN pip3 install -r requirements.txt

ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

CMD [ "flask", "run"]