# Endpoints de Usuario

Este documento describe los endpoints disponibles para la gestión de usuarios en el sistema AgroInsight.

## Autenticación y Autorización

### Registro de Usuario

::: app.user.infrastructure.api.create_user

### Confirmación de Registro

::: app.user.infrastructure.api.confirm_user_registration

### Reenvío de PIN de Confirmación

::: app.user.infrastructure.api.resend_confirmation_pin_endpoint

### Inicio de Sesión

::: app.user.infrastructure.api.login_for_access_token

### Verificación de Autenticación de Dos Factores

::: app.user.infrastructure.api.verify_login

### Reenvío de PIN de Autenticación de Dos Factores

::: app.user.infrastructure.api.resend_2fa_pin_endpoint

### Cierre de Sesión

::: app.user.infrastructure.api.logout

## Gestión de Contraseñas

### Recuperación de Contraseña

::: app.user.infrastructure.api.initiate_password_recovery

### Confirmación de PIN de Recuperación

::: app.user.infrastructure.api.confirm_recovery_pin

### Reenvío de PIN de Recuperación

::: app.user.infrastructure.api.resend_recovery_pin

### Restablecimiento de Contraseña

::: app.user.infrastructure.api.reset_password

## Gestión de Perfil de Usuario

### Obtener Usuario Actual

::: app.user.infrastructure.api.get_current_user

### Actualizar Información de Usuario

::: app.user.infrastructure.api.update_user_info

## Administración de Usuarios

### Crear Usuario por Administrador

::: app.user.infrastructure.api.create_user_by_admin

### Obtener Usuario por ID

::: app.user.infrastructure.api.get_user_by_id

### Listar Usuarios

::: app.user.infrastructure.api.list_users

### Actualizar Usuario por Administrador

::: app.user.infrastructure.api.admin_update_user

### Eliminar Usuario

::: app.user.infrastructure.api.deactivate_user
