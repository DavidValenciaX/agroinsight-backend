# Modelos del Módulo de Análisis de Suelo

## Modelos de Base de Datos

### Análisis de Suelo

::: app.soil_analysis.infrastructure.orm_models.SoilAnalysis

Modelo principal que representa un análisis de suelo completo.

### Clasificación de Suelo

::: app.soil_analysis.infrastructure.orm_models.SoilClassification

Modelo que representa una clasificación individual de tipo de suelo.

### Tipo de Suelo

::: app.soil_analysis.infrastructure.orm_models.SoilType

Modelo que representa los diferentes tipos de suelo que pueden ser detectados.

## Esquemas de Datos

### Probabilidades de Suelo

::: app.soil_analysis.domain.schemas.SoilProbabilities

### Respuesta de Clasificación

::: app.soil_analysis.domain.schemas.SoilClassificationResponse

### Respuesta del Servicio

::: app.soil_analysis.domain.schemas.PredictionServiceResponse

### Resultado de Análisis

::: app.soil_analysis.domain.schemas.SoilAnalysisResult
