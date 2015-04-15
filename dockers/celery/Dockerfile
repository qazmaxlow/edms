# sudo docker run --link mongo:mongo --link postgres:postgres --link rabbitmq:rabbitmq -t -i -v ~/src/entrak:/srv entrak_dms/celeryd

FROM ubuntu:14.10

RUN apt-get update && apt-get install -y python-pip
RUN apt-get install -y libmysqlclient-dev libpq-dev
RUN apt-get install -y python-dev libxslt1-dev libxml2-dev

RUN apt-get install -y python-dateutil

ADD pip_requirements.txt pip_requirements.txt
RUN pip install -r pip_requirements.txt
RUN pip install python-dateutil --upgrade
RUN rm pip_requirements.txt

WORKDIR /srv
RUN mkdir -p /log/entrak/dms/celery

# OOPS the code need this directory
RUN mkdir -p /logs/entrak

RUN mkdir -p /srv/log/entrak/dms/celery

ENV C_FORCE_ROOT true
CMD ["/bin/bash"]
