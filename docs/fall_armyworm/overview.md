# Visión General del Módulo de Detección de Gusano Cogollero

## Introducción

El módulo de Detección de Gusano Cogollero es una parte crítica del sistema AgroInsight que utiliza inteligencia artificial para detectar y monitorear la presencia del gusano cogollero (Spodoptera frugiperda) en cultivos de maíz. Este módulo permite a los agricultores identificar tempranamente esta plaga y tomar medidas preventivas.

## Características Principales

### 1. Detección Automatizada

- Análisis de imágenes mediante deep learning
- Identificación de tres estados:
  - Hojas con presencia de larvas
  - Hojas dañadas por el gusano
  - Hojas saludables
- Niveles de confianza en la detección

### 2. Monitoreo Fitosanitario

- Registro de inspecciones periódicas
- Seguimiento del estado de los cultivos
- Historial de detecciones
- Observaciones y notas de campo

### 3. Procesamiento por Lotes

- Capacidad de procesar múltiples imágenes
- Procesamiento síncrono para lotes pequeños (≤15 imágenes)
- Procesamiento asíncrono para lotes grandes (>15 imágenes)
- Estado y seguimiento del procesamiento

### 4. Integración con Servicios Externos

- Conexión con servicio especializado de IA
- Almacenamiento en la nube de imágenes
- Análisis estadístico de resultados

## Flujo de Trabajo

1. **Captura de Imágenes**: Los usuarios toman fotografías de las hojas de maíz durante las tareas de monitoreo fitosanitario.

2. **Envío y Procesamiento**:
   - Las imágenes se envían al servidor
   - Se realiza la detección mediante IA
   - Se almacenan los resultados y las imágenes

3. **Análisis y Resultados**:
   - Visualización de resultados de detección
   - Estadísticas y probabilidades
   - Recomendaciones basadas en los hallazgos

## Integración con Otros Módulos

El módulo se integra con:

- **Módulo de Prácticas Culturales**: Para el registro de tareas de monitoreo
- **Módulo de Lotes**: Para la ubicación de las detecciones
- **Módulo de Fincas**: Para la gestión de permisos y acceso

## Tecnologías Utilizadas

- TensorFlow para el modelo de detección
- FastAPI para la API REST
- Cloudinary para almacenamiento de imágenes
- PostgreSQL para persistencia de datos

## Consideraciones de Uso

- Las imágenes deben ser claras y bien enfocadas
- Se recomienda tomar las fotos durante el día
- Cada imagen debe mostrar claramente las hojas de maíz
- El sistema funciona mejor con imágenes de alta resolución
