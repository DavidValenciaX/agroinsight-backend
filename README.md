# AgroInsight - Crecimiento sostenible del Maíz

Este es un proyecto que tiene como objetivo desarrollar una aplicación con arquitectura cliente-servidor, con servidor en la nube de Coolify y cliente móvil en Android, para el análisis de suelos, la detección temprana del gusano cogollero en cultivos de maíz, la integración de datos meteorológicos de una API externa y la generación de reportes y recomendaciones basados en el análisis de los datos recolectados, a través de la inteligencia artificial.

Este documento muestra cómo configurar el proyecto inicialmente.

## Requisitos

- Python 3.9+
- Poetry
- Docker

## Instalación

### Clona este repositorio

```bash
https://github.com/DavidValenciaX/agroinsight-backend
cd agroinsight-backend
```

### Instala las dependencias con Poetry

```bash
poetry install
```

## Uso

### Desarrollo

Para desarrollar y ejecutar la aplicación localmente:

```bash
poetry run uvicorn app.main:app --reload
```

### Despliegue

Construye la imagen de Docker:

```bash
docker build -t agroinsight-backend .
```

Ejecuta el contenedor de Docker:

```bash
docker run -p 8000:8000 agroinsight-backend
```

La API estará disponible en `http://localhost:8000`

## Contribución

Si deseas contribuir al proyecto, por favor sigue las siguientes pautas:

1. Crea una nueva rama (`git checkout -b feature/nueva-caracteristica`).
2. Realiza tus cambios y haz commit (`git commit -m 'Agrega nueva característica'`).
3. Empuja tu rama (`git push origin feature/nueva-caracteristica`).
4. Abre un Pull Request.

## Licencia

Este proyecto está licenciado bajo la Licencia MIT.
