
# AgroInsight - Backend

## Descripción del Proyecto

AgroInsight es una aplicación innovadora diseñada para optimizar el cultivo de maíz en la región del Huila, Colombia. Utiliza una arquitectura cliente-servidor, con el backend desplegado en la plataforma Railway y clientes móvil (Android) y web.

### Características Principales

- Análisis de suelos mediante procesamiento de imágenes
- Detección temprana del gusano cogollero utilizando visión artificial
- Integración de datos meteorológicos de OpenWeatherMap
- Generación de reportes y recomendaciones personalizadas basadas en IA
- Funcionalidad offline y sincronización de datos

## Tecnologías Utilizadas

- **Backend:** FastAPI 0.112.1, Python 3.12
- **Base de Datos:** MySQL 8.0
- **ORM:** SQLAlchemy 2.0.32
- **Contenedorización:** Docker
- **IA y Procesamiento de Imágenes:** TensorFlow 2.16.1, OpenCV 4.10.0
- **Despliegue:** Railway

## Requisitos del Sistema

- Python 3.12+
- Docker
- Poetry 1.8.3+
- Git

## Configuración del Entorno de Desarrollo

1. Clonar el repositorio:

   ```bash
   git clone https://github.com/DavidValenciaX/agroinsight-backend.git
   cd agroinsight-backend
   ```

2. Instalar Poetry (si no está instalado):

   ```bash
   pip install poetry
   ```

3. Instalar dependencias del proyecto:

   ```bash
   poetry install
   ```

4. Configurar variables de entorno:
   Copiar el archivo `.env.example` a `.env` y configurar las variables necesarias.

## Ejecución del Proyecto

### Desarrollo Local

1. Activar el entorno virtual:

   ```bash
   poetry shell
   ```

2. Ejecutar el servidor de desarrollo:

   ```bash
   poetry run uvicorn app.main:app --reload
   ```

La API estará disponible en `http://localhost:8000`.

## Estructura del Proyecto

```bash
agroinsight-backend/
├── .github/                    # Configuraciones de GitHub
├── app/                        # Código fuente de la aplicación
│   ├── main.py                 # Punto de entrada de la aplicación
│   └── __init__.py
├── .dockerignore
├── .env                        # Variables de entorno (no incluir en el repositorio)
├── .gitignore
├── Dockerfile                  # Configuración para la construcción de la imagen Docker
├── LICENSE                     # Licencia del proyecto (MIT)
├── pyproject.toml              # Configuración de Poetry y dependencias
├── README.md                   # Este archivo
```

## Flujo de Trabajo de Desarrollo

1. Crear una nueva rama para cada característica o corrección (`git checkout -b feature/new_feature`)
2. Desarrollar y probar los cambios localmente.
3. Asegurar que el código pase todas las pruebas y linters.
4. Realice un commit siguiendo el estandar de conventional commits (`git commit -m 'feat: Add some new_feature'`).
5. Realice push a la rama de la nueva feature (`git push origin feature/new_feature`).
6. Crear un Pull Request siguiendo la plantilla proporcionada.
7. Esperar la revisión y aprobación antes de fusionar.

## Despliegue

El despliegue se realiza automáticamente en Railway al fusionar cambios en la rama `main`.

## Pruebas

Ejecutar las pruebas unitarias:

```bash
poetry run pytest
```

## Contribución

Las contribuciones son bienvenidas. Por favor, siga estas pautas:

1. Bifurque el repositorio.
2. Cree una rama para su característica (`git checkout -b feature/amazing_feature`).
3. Realice sus cambios y haga commit (`git commit -m 'feat: Add some amazing_feature'`).
4. Empuje a la rama (`git push origin feature/amazing_feature`).
5. Abra un Pull Request.

## Licencia

Este proyecto está licenciado bajo la Licencia MIT. Consulte el archivo `LICENSE` para más detalles.

## Contacto

David Valencia - [davidvalencia0526@gmail.com]

Enlace del Proyecto: [https://github.com/DavidValenciaX/agroinsight-backend]
