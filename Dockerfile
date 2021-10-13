FROM python:3.7
MAINTAINER Ruslan Tolkun uulu "tggrmi@gmail.com"
ENV PYTHONUNBUFFERED 1

RUN mkdir /app
WORKDIR /app

COPY requirements/base.txt /app/
RUN pip install -r base.txt
COPY . /app/
COPY ./entrypoint.sh /entrypoint.sh

RUN chmod 777 /entrypoint.sh
ENTRYPOINT [ "/entrypoint.sh" ]