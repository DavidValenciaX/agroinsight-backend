# Casos de Uso de Finca

Este documento describe los casos de uso relacionados con la gestión de fincas en el sistema AgroInsight.

## Gestión de Fincas

### Caso de Uso: Creación de Finca

::: app.farm.application.create_farm_use_case.CreateFarmUseCase

Este caso de uso maneja la lógica de negocio para la creación de nuevas fincas, incluyendo la validación de datos y la asignación del rol de administrador.

### Caso de Uso: Listar Fincas

::: app.farm.application.list_farms_use_case.ListFarmsUseCase

### Caso de Uso: Asignar Usuarios a Finca

::: app.farm.application.assign_users_to_farm_use_case.AssignUsersToFarmUseCase

## Servicios de Finca

### Servicio de Finca

::: app.farm.application.services.farm_service.FarmService

Este servicio proporciona funcionalidades comunes utilizadas por varios casos de uso, como la verificación de roles y permisos.
