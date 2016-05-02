FROM centos:7

EXPOSE 5000
ENV IPFS_GATEWAY https://localhost:8080
ENTRYPOINT ["/start.sh"]


RUN yum install -y epel-release && \
    yum install -y python-pip nginx uwsgi uwsgi-plugin-python


RUN pip install base58 flask

RUN ln -sf /dev/stdout /var/log/nginx/access.log && \
	ln -sf /dev/stderr /var/log/nginx/error.log

COPY wsgi.conf /
COPY proxy.conf /

COPY start.sh /
COPY nginx.conf /
COPY app.py /


