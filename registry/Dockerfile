FROM centos:7

EXPOSE 5000
ENV IPFS_GATEWAY https://localhost:8080
ENTRYPOINT ["/start.sh"]


RUN yum install -y epel-release && \
    yum install -y python-pip nginx uwsgi uwsgi-plugin-python


RUN pip install base58 flask

RUN curl -Lsk https://github.com/Yelp/dumb-init/releases/download/v1.0.2/dumb-init_1.0.2_amd64 > /usr/local/bin/dumb-init && \
    chmod +x /usr/local/bin/dumb-init

RUN ln -sf /dev/stdout /var/log/nginx/access.log && \
	ln -sf /dev/stderr /var/log/nginx/error.log

COPY wsgi.conf /
COPY proxy.conf /
COPY locations.conf /
COPY https.conf /

COPY start.sh /
COPY nginx.conf /
COPY app.py /


