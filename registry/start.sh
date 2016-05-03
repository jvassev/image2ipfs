#!/bin/bash

IPFS=${IPFS_GATEWAY%%/}

# improvised templating engine
sed -i "s|#IPFS#|$IPFS|g" /proxy.conf
cat /proxy.conf

if [ x$HTTPS_CERT != 'x' ];then
    sed -i "s|#HTTPS#|include /https.conf;|g" /nginx.conf
    sed -i "s|#HTTPS_KEY#|$HTTPS_KEY|g" /https.conf
    sed -i "s|#HTTPS_CERT#|$HTTPS_CERT|g" /https.conf
    cat /https.conf
fi

cat /nginx.conf

# TODO manage processes with supervisor
uwsgi --daemonize /var/log/uwsgi.log --ini /wsgi.conf

nginx -c /nginx.conf -g "daemon off;"
