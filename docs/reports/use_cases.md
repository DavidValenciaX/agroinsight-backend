# Casos de Uso del Módulo de Reportes

## Reportes Financieros

### Caso de Uso: Generar Reporte Financiero

::: app.reports.application.generate_financial_report_use_case.GenerateFinancialReportUseCase

Este caso de uso maneja la lógica de negocio para la generación de reportes financieros detallados, incluyendo:

- Validación de permisos del usuario
- Cálculo de costos por tarea
- Cálculo de costos e ingresos por cultivo
- Cálculo de totales por lote
- Generación del reporte financiero completo de la finca

El caso de uso permite:

- Filtrar por período específico
- Filtrar por lote específico (opcional)
- Filtrar por cultivo específico (opcional)
- Calcular costos totales, ingresos y ganancias netas
