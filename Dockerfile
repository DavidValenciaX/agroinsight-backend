# Usa una imagen base de Python
FROM python:3.12-slim

# Declara los ARGs para las variables de entorno que necesitas
ARG MYSQL_PUBLIC_URL
ARG SECRET_KEY

# Establece las variables de entorno usando los ARGs, con valores por defecto
ENV MYSQL_PUBLIC_URL=${MYSQL_PUBLIC_URL:-mysql://root:uykYedlFvprkpNRaLiFEHYXJHxDnTsMN@autorack.proxy.rlwy.net:15690/railway}
ENV SECRET_KEY=${SECRET_KEY:-AgroInsight2024!}

WORKDIR /code

# Copia y configura Poetry
COPY ./pyproject.toml ./poetry.lock* /code/

RUN pip install --upgrade pip && \
    pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev --no-root

# Copia la aplicación después de instalar las dependencias para aprovechar la cache de Docker
COPY ./app /code/app

# Comando para iniciar la aplicación
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]