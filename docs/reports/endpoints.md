# Endpoints del Módulo de Reportes

## Reportes Financieros

### Generar Reporte Financiero

::: app.reports.infrastructure.api.generate_financial_report

Endpoint principal para generar reportes financieros detallados. Permite:

- Filtrar por período específico
- Filtrar por lote o cultivo
- Agrupar resultados por diferentes criterios
- Aplicar filtros de costos
- Obtener análisis de rentabilidad

#### Parámetros de Agrupación

- `none`: Sin agrupación (por defecto)
- `task_type`: Agrupa por tipo de tarea
- `month`: Agrupa por mes
- `cost_type`: Agrupa por categoría de costo

[Ver documentación detallada](financial.md)

## Futuros Endpoints

- Endpoints de reportes de producción
- Endpoints de reportes de actividades
