# Usa una imagen base de Python
FROM python:3.12-slim AS builder

# Establece el directorio de trabajo
WORKDIR /code

# Instala las herramientas necesarias
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir poetry

# Copia solo los archivos necesarios para la instalación de dependencias
COPY pyproject.toml poetry.lock* ./

# Configura Poetry y instala las dependencias
RUN poetry config virtualenvs.create false && \
    poetry install --no-dev --no-root

# Segunda etapa: imagen final
FROM python:3.12-slim

WORKDIR /code

# Copia las dependencias instaladas desde la etapa del builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copia la aplicación
COPY ./app /code/app

# Comando para iniciar la aplicación
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]