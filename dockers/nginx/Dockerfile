# sudo docker run -p 8000:8000 --link uwsgi:uwsgi -v ~/src/entrak:/srv entrak_dms/test_server
FROM nginx:1.7.7
COPY test_nginx.conf /etc/nginx/conf.d/entrak_dms_nginx.conf
COPY en-trak.com.pem /etc/nginx/
COPY en-trak.com.key /etc/nginx/