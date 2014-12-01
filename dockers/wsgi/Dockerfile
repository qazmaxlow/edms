# Put this in the root folder of entrak git repo and run docker build -t entrak-dms/wsgi .
FROM ubuntu:14.04.1

RUN apt-get update && apt-get install -y python-pip
RUN apt-get install -y libmysqlclient-dev libpq-dev
RUN apt-get install -y python-dev libxslt1-dev libxml2-dev

ADD pip_requirements.txt pip_requirements.txt
RUN pip install -r pip_requirements.txt
RUN rm pip_requirements.txt

WORKDIR /srv
RUN mkdir -p /logs/entrak
