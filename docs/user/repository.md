# Documentación del Repositorio de Usuarios

## Visión General

El módulo `UserRepository` proporciona una interfaz para interactuar con la base de datos en relación con los usuarios y entidades relacionadas. Esta clase encapsula todas las operaciones de base de datos relacionadas con usuarios, incluyendo creación, lectura, actualización y eliminación (CRUD), así como operaciones específicas para la gestión de usuarios como confirmaciones, verificación de dos pasos y recuperación de contraseñas.

## Clase: UserRepository

### Constructor

::: app.user.infrastructure.sql_repository.UserRepository.__init__

### Métodos de Usuario

#### Obtener Usuario por Email

::: app.user.infrastructure.sql_repository.UserRepository.get_user_by_email

#### Obtener Usuario por ID

::: app.user.infrastructure.sql_repository.UserRepository.get_user_by_id

#### Obtener Usuario con Confirmación

::: app.user.infrastructure.sql_repository.UserRepository.get_user_with_confirmation

#### Obtener Usuario con Verificación de Dos Pasos

::: app.user.infrastructure.sql_repository.UserRepository.get_user_with_two_factor_verification

#### Obtener Usuario con Recuperación de Contraseña

::: app.user.infrastructure.sql_repository.UserRepository.get_user_with_password_recovery

#### Obtener Todos los Usuarios

::: app.user.infrastructure.sql_repository.UserRepository.get_all_users

#### Agregar Usuario

::: app.user.infrastructure.sql_repository.UserRepository.add_user

#### Actualizar Usuario

::: app.user.infrastructure.sql_repository.UserRepository.update_user

#### Eliminar Usuario

::: app.user.infrastructure.sql_repository.UserRepository.delete_user

### Métodos de Confirmación de Usuario

#### Agregar Confirmación de Usuario

::: app.user.infrastructure.sql_repository.UserRepository.add_user_confirmation

#### Actualizar Confirmación de Usuario

::: app.user.infrastructure.sql_repository.UserRepository.update_user_confirmation

#### Eliminar Confirmación de Usuario

::: app.user.infrastructure.sql_repository.UserRepository.delete_user_confirmation

### Métodos de Verificación de Dos Pasos

#### Agregar Verificación de Dos Pasos

::: app.user.infrastructure.sql_repository.UserRepository.add_two_factor_verification

#### Actualizar Verificación de Dos Pasos

::: app.user.infrastructure.sql_repository.UserRepository.update_two_factor_verification

#### Eliminar Verificación de Dos Pasos

::: app.user.infrastructure.sql_repository.UserRepository.delete_two_factor_verification

### Métodos de Recuperación de Contraseña

#### Agregar Recuperación de Contraseña

::: app.user.infrastructure.sql_repository.UserRepository.add_password_recovery

#### Actualizar Recuperación de Contraseña

::: app.user.infrastructure.sql_repository.UserRepository.update_password_recovery

#### Eliminar Recuperación de Contraseña

::: app.user.infrastructure.sql_repository.UserRepository.delete_password_recovery

### Métodos de Gestión de Tokens

#### Agregar Token a Lista Negra

::: app.user.infrastructure.sql_repository.UserRepository.blacklist_token

#### Verificar si un Token está en Lista Negra

::: app.user.infrastructure.sql_repository.UserRepository.is_token_blacklisted

### Métodos de Estado de Usuario

#### Obtener Estado por ID

::: app.user.infrastructure.sql_repository.UserRepository.get_state_by_id

#### Obtener Estado por Nombre

::: app.user.infrastructure.sql_repository.UserRepository.get_state_by_name

### Métodos de Rol

#### Obtener Rol por ID

::: app.user.infrastructure.sql_repository.UserRepository.get_role_by_id

#### Obtener Rol por Nombre

::: app.user.infrastructure.sql_repository.UserRepository.get_role_by_name

## Constantes

El módulo define las siguientes constantes:

- `ADMIN_ROLE_NAME`: Nombre del rol de administrador de finca.
- `WORKER_ROLE_NAME`: Nombre del rol de trabajador agrícola.
- `ACTIVE_STATE_NAME`: Nombre del estado activo de usuario.
- `LOCKED_STATE_NAME`: Nombre del estado bloqueado de usuario.
- `PENDING_STATE_NAME`: Nombre del estado pendiente de usuario.
- `INACTIVE_STATE_NAME`: Nombre del estado inactivo de usuario.

## Manejo de Errores

Todos los métodos que interactúan con la base de datos están envueltos en bloques try-except para manejar posibles errores. En caso de error, se realiza un rollback de la transacción y se imprime un mensaje de error. Los métodos que devuelven un valor booleano retornan `False` en caso de error, mientras que los métodos que devuelven un objeto retornan `None`.

## Mejores Prácticas

1. __Uso de Sesiones__: Siempre use la sesión de base de datos proporcionada al constructor para realizar operaciones de base de datos.
2. __Manejo de Transacciones__: Use `self.db.commit()` para confirmar cambios y `self.db.rollback()` en caso de error.
3. __Logging__: Considere reemplazar los `print` statements con un sistema de logging apropiado para un mejor seguimiento de errores en producción.
4. __Tipado__: El uso de type hints mejora la legibilidad y permite un mejor análisis estático del código.
5. __Documentación__: Mantenga los docstrings actualizados y detallados para facilitar el uso y mantenimiento del código.
