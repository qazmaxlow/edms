# Put this in the root folder of entrak git repo and run docker build -t entrak_dms/uwsgi .
# sudo docker run --name uwsgi --link mongo:mongo --link postgres:postgres -t -i -v ~/src/entrak:/srv entrak_dms/uwsgi
FROM entrakdms_celerybase

RUN apt-get install -y uwsgi uwsgi-plugin-python xfonts-75dpi

# ubuntu's one did not work for server version
Add wkhtmltox-0.12.1_linux-trusty-amd64.deb wkhtmltox-0.12.1_linux-trusty-amd64.deb 
RUN apt-get install -y xorg libssl-dev libxrender-dev libjpeg8-dev libjpeg8 fontconfig
RUN dpkg -i wkhtmltox-0.12.1_linux-trusty-amd64.deb

RUN mkdir -p /logs/entrak

EXPOSE 8080
#ADD uwsgi.ini uwsgi.ini
#CMD uwsgi --ini uwsgi.ini

