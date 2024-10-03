# Preguntas Frecuentes (FAQ)

## ¿Qué es AgroInsight?

AgroInsight es una aplicación de gestión agrícola diseñada para optimizar el cultivo de maíz en la región del Huila, Colombia. Utiliza tecnologías modernas como FastAPI, React Native, y TensorFlow para ofrecer funcionalidades avanzadas como análisis de suelos, detección de plagas, y recomendaciones personalizadas.

## ¿Cómo puedo empezar a contribuir al proyecto?

Para comenzar a contribuir, sigue estos pasos:

1. Clona el repositorio desde GitHub.
2. Configura tu entorno de desarrollo siguiendo la [Guía de Instalación](installation.md).
3. Revisa la [Guía de Contribución](../development/contributing.md) para entender las normas y el flujo de trabajo del proyecto.

## ¿Cuáles son los requisitos del sistema para ejecutar AgroInsight?

Los requisitos principales incluyen:

- Python 3.12 o superior
- Docker
- MySQL 8.0
- Poetry para la gestión de dependencias

Para más detalles, consulta la sección de [Requisitos del Sistema](/README.md).

## ¿Cómo se maneja la autenticación en AgroInsight?

AgroInsight utiliza autenticación de dos factores (2FA) para mejorar la seguridad. Los usuarios deben verificar su identidad mediante un PIN enviado a su correo electrónico. Para más detalles, revisa el endpoint `/login/verify` en la [documentación de la API](../fast-api-docs/overview.md).

## ¿Qué debo hacer si encuentro un error durante la instalación?

Si encuentras problemas durante la instalación, verifica lo siguiente:

- Asegúrate de que todas las dependencias están instaladas correctamente.
- Revisa que las variables de entorno en el archivo `.env` estén configuradas correctamente.
- Consulta la sección de [Solución de Problemas Comunes](installation.md) para más ayuda.

## ¿Cómo se gestionan los roles de usuario en el sistema?

Los roles de usuario se gestionan a través de la base de datos y se asignan durante la creación del usuario. Los roles determinan los permisos y accesos dentro del sistema. Para más información, revisa el módulo de usuarios en la [documentación del código](../user/overview.md).

## ¿Dónde puedo encontrar la documentación de la API?

La documentación de la API se genera automáticamente y está disponible en:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## ¿Cómo se despliega AgroInsight?

El despliegue se realiza automáticamente en la plataforma Railway al fusionar cambios en la rama `main`. Asegúrate de que todas las pruebas pasen antes de fusionar tus cambios. Para más detalles, consulta la sección de [Despliegue](../README.md).

## ¿Cómo puedo reportar un problema o sugerir una mejora?

Puedes reportar problemas o sugerir mejoras creando un issue en el [repositorio de GitHub](https://github.com/DavidValenciaX/agroinsight-backend). Asegúrate de proporcionar una descripción detallada y, si es posible, pasos para reproducir el problema.

## ¿Dónde puedo encontrar más información sobre las prácticas de codificación?

Revisa la [Guía de Estándares de Codificación](../development/coding_standards.md) para conocer las convenciones y prácticas recomendadas en el proyecto.

## ¿Cómo se gestionan las pruebas en AgroInsight?

Las pruebas se ejecutan utilizando `pytest`. Puedes ejecutar todas las pruebas con el comando `pytest` o pruebas específicas según sea necesario. Para más detalles, consulta la [Guía de Pruebas](../development/testing.md).
