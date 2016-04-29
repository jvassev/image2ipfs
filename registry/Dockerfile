FROM python:2.7.11

ENV IPFS_GATEWAY https://ipfs.io
RUN pip install base58 flask

#RUN pip install pyOpenSSL
#RUN openssl genrsa -des3 -passout pass:x -out server.pass.key 2048 && \
#    openssl rsa -passin pass:x -in server.pass.key -out server.key && \
#    rm server.pass.key && \
#    openssl req -new -key server.key -out server.csr -subj '/C=US/O=Internet/commonName=localhost/emailAddress=jvassev@gmail.com' && \
#    openssl x509 -req -days 3650 -in server.csr -signkey server.key -out server.crt

COPY app.py /

ENTRYPOINT ["python", "/app.py"]