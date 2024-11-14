# Modelos del Módulo de Detección de Gusano Cogollero

## Modelos de Base de Datos

### Monitoreo Fitosanitario

::: app.fall_armyworm.infrastructure.orm_models.MonitoreoFitosanitario

Modelo que representa un monitoreo fitosanitario completo.

### Detección de Gusano Cogollero

::: app.fall_armyworm.infrastructure.orm_models.FallArmywormDetection

Modelo que representa una detección individual del análisis de imagen.

## Enumeraciones

### Estado de Monitoreo

::: app.fall_armyworm.infrastructure.orm_models.EstadoMonitoreoEnum

### Resultado de Detección

::: app.fall_armyworm.infrastructure.orm_models.DetectionResultEnum

## Esquemas de Datos

### Probabilidades de Detección

::: app.fall_armyworm.domain.schemas.DetectionProbabilities

### Respuesta de Detección

::: app.fall_armyworm.domain.schemas.DetectionResponse

### Respuesta del Servicio de Predicción

::: app.fall_armyworm.domain.schemas.PredictionServiceResponse

### Resultado de Detección de Gusano Cogollero

::: app.fall_armyworm.domain.schemas.FallArmywormDetectionResult

### Creación de Monitoreo Fitosanitario

::: app.fall_armyworm.domain.schemas.MonitoreoFitosanitarioCreate

### Creación de Detección

::: app.fall_armyworm.domain.schemas.FallArmywormDetectionCreate
