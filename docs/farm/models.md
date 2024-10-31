# Modelos de Finca

Este documento describe los modelos utilizados para la gestión de fincas en el sistema AgroInsight.

## Modelos de Base de Datos

### Finca (Farm)

::: app.farm.infrastructure.orm_models.Farm

### Relación Usuario-Finca-Rol (UserFarmRole)

::: app.user.infrastructure.orm_models.UserFarmRole

## Esquemas de Datos

### Crear Finca

::: app.farm.domain.schemas.FarmCreate

### Respuesta de Finca

::: app.farm.domain.schemas.FarmResponse

### Respuesta Paginada de Fincas

::: app.farm.domain.schemas.PaginatedFarmListResponse

### Asignación de Usuarios por Email

::: app.farm.domain.schemas.FarmUserAssignmentByEmail

### Respuesta Paginada de Usuarios de Finca

::: app.farm.domain.schemas.PaginatedFarmUserListResponse
