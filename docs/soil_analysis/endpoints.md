# Endpoints del Módulo de Análisis de Suelo

## Análisis de Imágenes

### Predecir Tipo de Suelo

::: app.soil_analysis.infrastructure.api.predict_images

Endpoint principal para realizar el análisis de suelo mediante imágenes. Soporta procesamiento síncrono y asíncrono según la cantidad de imágenes.

### Probar Conexión con Servicio

::: app.soil_analysis.infrastructure.api.test_connection

Endpoint para verificar la disponibilidad del servicio de análisis de imágenes.

## Consulta de Resultados

### Obtener Estado de Procesamiento

::: app.soil_analysis.infrastructure.api.get_processing_status

Endpoint para consultar el estado actual del procesamiento de un análisis.

### Obtener Resultados de Análisis

::: app.soil_analysis.infrastructure.api.get_analysis_results

Endpoint para obtener los resultados detallados de un análisis específico.
