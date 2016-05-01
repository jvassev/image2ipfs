#!/bin/bash

IPFS=${IPFS_GATEWAY//https:\/\//}
IPFS=${IPFS//http:\/\//}
IPFS=${IPFS%%/}

echo $IPFS '==================='

# improvised templating engine
sed -i  "s|@IPFS@|$IPFS|g" /nginx.conf

cat /nginx.conf

# TODO manage processes with upervisor
nginx -c /nginx.conf

python /app.py