FROM centos:7

EXPOSE 5000
ENV IPFS_GATEWAY https://localhost:8080
ENTRYPOINT ["/start.sh"]


RUN yum install -y epel-release && \
    yum install -y python-pip nginx


RUN pip install base58 flask


COPY app.py /
COPY nginx.conf /
COPY proxy.conf /
COPY start.sh /

