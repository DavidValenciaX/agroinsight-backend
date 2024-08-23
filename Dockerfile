FROM python:3.12-slim

# Instalación de dependencias del sistema (si es necesario)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

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