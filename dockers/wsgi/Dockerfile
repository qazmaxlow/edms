# Put this in the root folder of entrak git repo and run docker build -t entrak-dms/wsgi .
FROM ubuntu:14.04.1

RUN apt-get update && apt-get install -y python-pip
RUN apt-get install -y libmysqlclient-dev libpq-dev
RUN apt-get install -y python-dev libxslt1-dev libxml2-dev

ADD . /srv
ADD dockers/wsgi/settings.py /srv/entrak/settings.py
WORKDIR /srv

RUN pip install -r pip_requirements.txt
RUN mkdir -p /logs/entrak
