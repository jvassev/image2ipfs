FROM nginx:1.10.0

ENV PORT 9090
ENV IPFS localhost:8080

COPY nginx.conf /
COPY start.sh /

ENTRYPOINT ["/start.sh"]