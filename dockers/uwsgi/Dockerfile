# Put this in the root folder of entrak git repo and run docker build -t entrak_dms/uwsgi .
# sudo docker run --name uwsgi --link mongo:mongo --link postgres:postgres -t -i -v ~/src/entrak:/srv entrak_dms/uwsgi
FROM ubuntu:14.10

RUN apt-get update && apt-get install -y python-pip
RUN apt-get install -y libmysqlclient-dev libpq-dev
RUN apt-get install -y python-dev libxslt1-dev libxml2-dev
RUN apt-get install -y uwsgi uwsgi-plugin-python
#RUN apt-get install -y openssl build-essential xorg libssl-dev
#RUN apt-get install -y build-essential xorg libssl-dev libxrender-dev
#RUN apt-get install -y wkhtmltopdf

Add wkhtmltox-0.12.1_linux-trusty-amd64.deb .
RUN apt-get install -y xorg libssl-dev libxrender-dev libjpeg8-dev libjpeg8 fontconfig
RUN dpkg -i wkhtmltox-0.12.1_linux-trusty-amd64.deb 

# ubuntu's one did not work for server version
Add wkhtmltox-0.12.1_linux-trusty-amd64.deb .
RUN apt-get install -y xorg libssl-dev libxrender-dev libjpeg8-dev libjpeg8 fontconfig
RUN dpkg -i wkhtmltox-0.12.1_linux-trusty-amd64.deb

ADD pip_requirements.txt pip_requirements.txt
RUN pip install -r pip_requirements.txt
RUN rm pip_requirements.txt

RUN mkdir -p /logs/entrak

EXPOSE 8080
ADD uwsgi.ini uwsgi.ini
CMD uwsgi --ini uwsgi.ini
