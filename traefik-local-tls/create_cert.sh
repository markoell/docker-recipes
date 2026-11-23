#!/bin/bash

openssl req -x509 -out ./certs/local.crt -keyout ./certs/local.key \
  -newkey rsa:2048 -nodes -sha256 -days 825 \
  -subj '/CN=*.docker.localhost' \
  -addext 'subjectAltName=DNS:*.docker.localhost,DNS:docker.localhost,DNS:localhost' \
  -addext 'keyUsage=digitalSignature,keyEncipherment' \
  -addext 'extendedKeyUsage=serverAuth' \
  -addext 'basicConstraints=critical,CA:FALSE'