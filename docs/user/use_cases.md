# Casos de Uso de Usuario

Este documento describe los casos de uso relacionados con la gestión de usuarios en el sistema AgroInsight.

## Proceso de Creación de Usuario

### Caso de Uso: Creación de Usuario

::: app.user.application.user_creation_process.user_creation_use_case.UserCreationUseCase

Este caso de uso maneja la lógica de negocio para el registro de nuevos usuarios, incluyendo la validación de datos, la creación del usuario en la base de datos, y el envío de correos de confirmación.

#### Métodos Principales

##### execute

::: app.user.application.user_creation_process.user_creation_use_case.UserCreationUseCase.execute

##### create_and_send_confirmation

::: app.user.application.user_creation_process.user_creation_use_case.UserCreationUseCase.create_and_send_confirmation

##### send_confirmation_email

::: app.user.application.user_creation_process.user_creation_use_case.UserCreationUseCase.send_confirmation_email
