#!/bin/bash

IPFS=${IPFS_GATEWAY//https:\/\//}
IPFS=${IPFS//http:\/\//}
IPFS=${IPFS%%/}

# improvised templating engine
sed -i  "s|@IPFS@|$IPFS|g" /nginx.conf

cat /nginx.conf

# TODO manage processes with upervisor
uwsgi --daemonize /var/log/uwsgi.log --ini /wsgi.conf

nginx -c /nginx.conf -g "daemon off;"