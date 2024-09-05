#!/bin/bash

# Construir la imagen Docker
docker build -t agroinsight-backend .

# Ejecutar la aplicación
docker run -p $PORT:8000 agroinsight-backend