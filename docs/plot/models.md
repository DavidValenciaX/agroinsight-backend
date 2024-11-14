# Modelos del Módulo de Lotes

Este documento describe los modelos utilizados para la gestión de lotes en el sistema AgroInsight.

## Modelos de Base de Datos

### Lote (Plot)

::: app.plot.infrastructure.orm_models.Plot

Modelo principal que representa un lote o parcela agrícola dentro de una finca.

## Esquemas de Datos

### Crear Lote

::: app.plot.domain.schemas.PlotCreate

Esquema para la creación de nuevos lotes.

### Respuesta de Lote

::: app.plot.domain.schemas.PlotResponse

Esquema para la respuesta con información de un lote.

### Respuesta Paginada de Lotes

::: app.plot.domain.schemas.PaginatedPlotListResponse

Esquema para la respuesta paginada de listas de lotes.

## Relaciones

Los lotes mantienen relaciones con:

- Fincas (Farm): Relación padre-hijo
- Cultivos (Crop): Relación uno a muchos
- Prácticas Culturales (CulturalTask): Relación uno a muchos
