# Modelos del Módulo de Costos

## Modelos de Base de Datos

### Costo de Mano de Obra (LaborCost)

::: app.costs.infrastructure.orm_models.LaborCost

Modelo que representa los costos de mano de obra asociados a una tarea cultural.

### Categoría de Insumo Agrícola (AgriculturalInputCategory)

::: app.costs.infrastructure.orm_models.AgriculturalInputCategory

Modelo que representa las categorías de insumos agrícolas disponibles.

### Insumo Agrícola (AgriculturalInput)

::: app.costs.infrastructure.orm_models.AgriculturalInput

Modelo que representa los insumos agrícolas y sus características.

### Uso de Insumo en Tarea (TaskInput)

::: app.costs.infrastructure.orm_models.TaskInput

Modelo que registra el uso de insumos en tareas específicas.

### Tipo de Maquinaria (MachineryType)

::: app.costs.infrastructure.orm_models.MachineryType

Modelo que representa los diferentes tipos de maquinaria agrícola.

### Maquinaria Agrícola (AgriculturalMachinery)

::: app.costs.infrastructure.orm_models.AgriculturalMachinery

Modelo que representa la maquinaria agrícola disponible.

### Uso de Maquinaria en Tarea (TaskMachinery)

::: app.costs.infrastructure.orm_models.TaskMachinery

Modelo que registra el uso de maquinaria en tareas específicas.

## Esquemas de Datos

### Creación de Costo de Mano de Obra

::: app.costs.domain.schemas.LaborCostCreate

### Creación de Uso de Insumo

::: app.costs.domain.schemas.TaskInputCreate

### Creación de Uso de Maquinaria

::: app.costs.domain.schemas.TaskMachineryCreate

### Creación de Costos de Tarea

::: app.costs.domain.schemas.TaskCostsCreate

### Respuesta de Registro de Costos

::: app.costs.domain.schemas.CostRegistrationResponse

### Respuesta de Categoría de Insumo

::: app.costs.domain.schemas.AgriculturalInputCategoryResponse

### Respuesta de Insumo Agrícola

::: app.costs.domain.schemas.AgriculturalInputResponse

### Respuesta de Tipo de Maquinaria

::: app.costs.domain.schemas.MachineryTypeResponse

### Respuesta de Maquinaria Agrícola

::: app.costs.domain.schemas.AgriculturalMachineryResponse
