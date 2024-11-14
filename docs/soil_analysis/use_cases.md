# Casos de Uso del Módulo de Análisis de Suelo

## Análisis de Imágenes

### Caso de Uso: Análisis de Suelo

::: app.soil_analysis.application.soil_analysis_use_case.SoilAnalysisUseCase

Este caso de uso maneja el procesamiento síncrono de imágenes para análisis de suelo.

### Caso de Uso: Análisis en Segundo Plano

::: app.soil_analysis.application.soil_analysis_background_use_case.SoilAnalysisBackgroundUseCase

Este caso de uso maneja el procesamiento asíncrono de grandes lotes de imágenes.

## Consulta de Resultados

### Caso de Uso: Obtener Estado de Análisis

::: app.soil_analysis.application.get_analysis_status_use_case.GetAnalysisStatusUseCase

### Caso de Uso: Obtener Análisis

::: app.soil_analysis.application.get_analysis_use_case.GetAnalysisUseCase

## Repositorio

### Repositorio de Análisis de Suelo

::: app.soil_analysis.infrastructure.sql_repository.SoilAnalysisRepository

Este repositorio maneja todas las operaciones de base de datos relacionadas con el análisis de suelo.
