# Casos de Uso del Módulo de Lotes

Este documento describe los casos de uso relacionados con la gestión de lotes en el sistema AgroInsight.

## Gestión de Lotes

### Caso de Uso: Creación de Lote

::: app.plot.application.create_plot_use_case.CreatePlotUseCase

Este caso de uso maneja la lógica de negocio para la creación de nuevos lotes, incluyendo:

- Validación de permisos del usuario
- Verificación de la existencia de la finca
- Validación de datos del lote
- Creación del registro en la base de datos

### Caso de Uso: Listar Lotes por Finca

::: app.plot.application.list_plots_use_case.ListPlotsUseCase

Este caso de uso gestiona la obtención paginada de lotes pertenecientes a una finca específica.
