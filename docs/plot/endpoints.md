# Endpoints del Módulo de Lotes

Este documento describe los endpoints disponibles para la gestión de lotes en el sistema AgroInsight.

## Gestión de Lotes

### Crear Lote

::: app.plot.infrastructure.api.create_plot

Endpoint para crear un nuevo lote en una finca específica.

### Listar Lotes por Finca

::: app.plot.infrastructure.api.list_plots_by_farm

Endpoint para obtener una lista paginada de los lotes pertenecientes a una finca.

## Estructura de Rutas

El módulo de lotes utiliza el prefijo `/plot` para todos sus endpoints y está etiquetado como "plot" en la documentación de la API.

## Autenticación y Autorización

Todos los endpoints requieren autenticación mediante JWT y verifican los permisos del usuario sobre la finca a la que pertenece el lote.
