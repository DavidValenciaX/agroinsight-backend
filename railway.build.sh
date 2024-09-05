#!/bin/bash

# Construir la imagen Docker
docker build -t agroinsight-backend \
  --build-arg MYSQL_PUBLIC_URL=$MYSQL_PUBLIC_URL \
  --build-arg SECRET_KEY=$SECRET_KEY \
  .

# Ejecutar la aplicación
docker run -p $PORT:8000 \
  -e MYSQL_PUBLIC_URL=$MYSQL_PUBLIC_URL \
  -e SECRET_KEY=$SECRET_KEY \
  agroinsight-backend