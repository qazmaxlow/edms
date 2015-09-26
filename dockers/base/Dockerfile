FROM ubuntu:14.10

RUN apt-get update && apt-get install -y python-pip
RUN apt-get install -y libmysqlclient-dev libpq-dev
RUN apt-get install -y python-dev libxslt1-dev libxml2-dev
RUN apt-get install -y freetds-dev

ADD pip_requirements.txt pip_requirements.txt
RUN pip install -r pip_requirements.txt
RUN rm pip_requirements.txt

RUN mkdir -p /logs/entrak

WORKDIR /srv
