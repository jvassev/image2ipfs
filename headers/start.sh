#!/bin/bash

# improvized templating engine
sed -i  "s|@IPFS@|$IPFS|g" /nginx.conf

sed -i  "s|@PORT@|$PORT|g" /nginx.conf

cat /nginx.conf

nginx -c /nginx.conf -g"daemon off;"