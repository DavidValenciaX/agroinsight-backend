# Guía de Instalación de AgroInsight

Esta guía proporciona instrucciones detalladas para configurar el entorno de desarrollo del proyecto AgroInsight. Sigue cada paso cuidadosamente para asegurar una instalación correcta y completa.

## Prerrequisitos

Antes de comenzar, asegúrate de tener instalado lo siguiente:

1. **Python 3.12 o superior**: Descarga e instala desde [python.org](https://www.python.org/downloads/).
2. **VS Code**: Descarga e instala desde [code.visualstudio.com](https://code.visualstudio.com/).
3. **MySQL 8.0**: Descarga e instala desde [dev.mysql.com](https://dev.mysql.com/downloads/mysql/).
4. **MySQL Workbench**: Descarga e instala desde [dev.mysql.com](https://dev.mysql.com/downloads/workbench/).
5. **pip**: Generalmente se instala con Python. Verifica con `pip --version`.
6. **Poetry**: Instala ejecutando `pip install poetry`.
7. **Git**: Descarga e instala desde [git-scm.com](https://git-scm.com/).
8. **Cuenta de GitHub**: Crea una cuenta en [github.com](https://github.com/).
9. **Docker Desktop**: Descarga e instala desde [docker.com](https://www.docker.com/products/docker-desktop).

## Pasos de Instalación del proyecto

### 1. Clonar los Repositorios

```bash
git clone https://github.com/DavidValenciaX/agroinsight-backend.git
cd agroinsight-backend
```

### 2. Configurar el Entorno Virtual para el Backend

```bash
poetry config virtualenvs.in-project true
poetry install
```

### 3. Instalar Dependencias del Backend

```bash
poetry install
```

### 4. Configurar Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto backend y añade las siguientes variables:

```env
MYSQL_PUBLIC_URL=mysql://user:password@host:port/database
SECRET_KEY=tu_clave_secreta
GMAIL_USER=tu_correo@gmail.com
GMAIL_APP_PASSWORD=tu_contraseña_de_aplicacion
```

Solicita los valores reales a un miembro del equipo.

### 5. Correr el servidor Backend

```bash
poetry run uvicorn app.main:app --reload
```

## Verificación de la Instalación

1. Backend: Visita `http://localhost:8000/docs` para ver la documentación Swagger de la API.

## Solución de Problemas Comunes

- **Problemas con dependencias de Python**: Asegúrate de usar Python 3.12 y que el entorno virtual esté activado.
- **Errores de base de datos**: Verifica que el contenedor Docker de MySQL esté corriendo y las credenciales en `.env` sean correctas.
- **Problemas con TensorFlow o OpenCV**: Asegúrate de que tu sistema cumple con los requisitos de hardware para IA.

## Próximos Pasos

- Revisa la [Guía de Inicio Rápido](getting_started.md) para comenzar a desarrollar.
- Familiarízate con la [estructura del proyecto y los estándares de código](../development/coding_standards.md).
- Configura tu entorno de desarrollo siguiendo las [mejores prácticas del equipo](../development/contributing.md).

Para cualquier problema adicional, consulta la [sección de FAQ](faq.md) o contacta al equipo de desarrollo a través de Slack.
