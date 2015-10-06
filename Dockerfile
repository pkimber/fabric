FROM ubuntu:14.04
MAINTAINER "Patrick Kimber" <code@pkimber.net>

# Prerequisites
RUN \
  apt-get update && \
  apt-get -y upgrade && \
  apt-get install -y python python-pip python-dev

# RUN apt-get install -y python python-dev python-distribute
# python-pip
# RUN mkdir /code
# WORKDIR /code
# ADD requirements.txt /code/
RUN apt-get install -y libpq-dev postgresql-client-9.3
ADD . /code/
RUN pip install -r code/requirements.txt
