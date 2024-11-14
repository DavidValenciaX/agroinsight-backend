# Casos de Uso del Módulo de Detección de Gusano Cogollero

## Detección y Análisis

### Caso de Uso: Detectar Gusano Cogollero

::: app.fall_armyworm.application.detect_fall_armyworm_use_case.DetectFallArmywormUseCase

Este caso de uso maneja el procesamiento síncrono de imágenes para la detección del gusano cogollero.

### Caso de Uso: Detectar Gusano Cogollero en Segundo Plano

::: app.fall_armyworm.application.detect_fall_armyworm_background_use_case.DetectFallArmywormBackgroundUseCase

Este caso de uso maneja el procesamiento asíncrono de grandes lotes de imágenes.

## Consulta de Resultados

### Caso de Uso: Obtener Estado de Monitoreo

::: app.fall_armyworm.application.get_monitoring_status_use_case.GetMonitoringStatusUseCase

### Caso de Uso: Obtener Resultados de Monitoreo

::: app.fall_armyworm.application.get_monitoring_use_case.GetMonitoringUseCase

## Repositorio

### Repositorio de Gusano Cogollero

::: app.fall_armyworm.infrastructure.sql_repository.FallArmywormRepository

Este repositorio maneja todas las operaciones de base de datos relacionadas con el monitoreo y detección del gusano cogollero.
