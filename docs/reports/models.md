# Modelos del Módulo de Reportes

## Esquemas de Datos

### Costo de Tarea

::: app.reports.domain.schemas.TaskCost

Modelo que representa los costos asociados a una tarea específica.

### Finanzas de Cultivo

::: app.reports.domain.schemas.CropFinancials

Modelo que representa la información financiera detallada de un cultivo.

### Finanzas de Lote

::: app.reports.domain.schemas.PlotFinancials

Modelo que representa la información financiera completa de un lote.

### Reporte Financiero de Finca

::: app.reports.domain.schemas.FarmFinancialReport

Modelo que representa el reporte financiero completo de una finca.

## Repositorio

### Repositorio de Reportes Financieros

::: app.reports.infrastructure.sql_repository.FinancialReportRepository

Repositorio que maneja todas las operaciones de base de datos necesarias para la generación de reportes financieros.
