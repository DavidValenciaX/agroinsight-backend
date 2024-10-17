# Casos de Uso de Usuario

Este documento describe los casos de uso relacionados con la gestión de usuarios en el sistema AgroInsight.

## Proceso de Creación de Usuario

### Caso de Uso: Creación de Usuario

::: app.user.application.user_register_process.user_register_use_case.UserRegisterUseCase

Este caso de uso maneja la lógica de negocio para el registro de nuevos usuarios, incluyendo la validación de datos, la creación del usuario en la base de datos, y el envío de correos de confirmación.

#### Métodos Principales de creación de usuario

##### register_user

::: app.user.application.user_register_process.user_register_use_case.UserRegisterUseCase.register_user

##### send_confirmation_email

::: app.user.application.user_register_process.user_register_use_case.UserRegisterUseCase.send_confirmation_email

### Caso de Uso: Confirmación de Usuario

::: app.user.application.user_register_process.confirmation_use_case.ConfirmationUseCase

Este caso de uso maneja la lógica de negocio para confirmar el registro de usuarios mediante un PIN, incluyendo la validación del PIN, la activación del usuario y la gestión de intentos fallidos.

#### Métodos Principales de confirmación de usuario

##### confirm_user

::: app.user.application.user_register_process.confirmation_use_case.ConfirmationUseCase.confirm_user

### Caso de Uso: Reenvío de Confirmación

::: app.user.application.user_register_process.resend_confirmation_use_case.ResendConfirmationUseCase

Este caso de uso maneja la lógica de negocio para reenviar PINs de confirmación a usuarios que están en proceso de registro.

#### Métodos Principales de reenvío de confirmación

##### resend_confirmation

::: app.user.application.user_register_process.resend_confirmation_use_case.ResendConfirmationUseCase.resend_confirmation

## Proceso de Inicio de Sesión

### Caso de Uso: Inicio de Sesión

::: app.user.application.login_process.login_use_case.LoginUseCase

Este caso de uso maneja la lógica de negocio para el inicio de sesión de usuarios, incluyendo la validación de credenciales, el manejo de intentos fallidos, y la generación de PIN para autenticación de dos factores.

#### Métodos Principales de inicio de sesión

##### login_user

::: app.user.application.login_process.login_use_case.LoginUseCase.login_user

### Caso de Uso: Verificación de Autenticación de Dos Factores

::: app.user.application.login_process.verify_2fa_use_case.VerifyUseCase

Este caso de uso maneja el proceso de verificación del PIN de autenticación de dos factores, incluyendo la validación del estado del usuario, la verificación del PIN, y el manejo de intentos fallidos.

#### Métodos Principales de verificación de autenticación de dos factores

##### verify_2fa

::: app.user.application.login_process.verify_2fa_use_case.VerifyUseCase.verify_2fa

### Caso de Uso: Reenvío de PIN de Verificación en Dos Pasos

::: app.user.application.login_process.resend_2fa_use_case.Resend2faUseCase

Este caso de uso maneja el proceso de reenvío del PIN de verificación en dos pasos, incluyendo la validación del estado del usuario, la verificación de solicitudes recientes, y la generación y envío de un nuevo PIN.

#### Métodos Principales de reenvío de PIN de verificación en dos pasos

##### resend_2fa

::: app.user.application.login_process.resend_2fa_use_case.Resend2faUseCase.resend_2fa

## Proceso de Recuperación de Contraseña

### Caso de Uso: Recuperación de Contraseña

::: app.user.application.password_recovery_process.password_recovery_use_case.PasswordRecoveryUseCase

Este caso de uso maneja el proceso de recuperación de contraseña, incluyendo la generación y envío de PIN, validación del estado del usuario y gestión de solicitudes recientes.

#### Métodos Principales de recuperación de contraseña

##### recovery_password

::: app.user.application.password_recovery_process.password_recovery_use_case.PasswordRecoveryUseCase.recovery_password

### Caso de Uso: Confirmación de PIN de Recuperación

::: app.user.application.password_recovery_process.confirm_recovery_use_case.ConfirmRecoveryPinUseCase

Este caso de uso maneja el proceso de confirmación del PIN de recuperación, incluyendo la validación del estado del usuario, la verificación del PIN, y el manejo de intentos fallidos.

#### Métodos Principales de confirmación de PIN de recuperación

##### confirm_recovery

::: app.user.application.password_recovery_process.confirm_recovery_use_case.ConfirmRecoveryPinUseCase.confirm_recovery

### Caso de Uso: Reenvío de PIN de Recuperación

::: app.user.application.password_recovery_process.resend_recovery_use_case.ResendRecoveryUseCase

Este caso de uso maneja el proceso de reenvío del PIN de recuperación, incluyendo la validación del estado del usuario, la verificación de solicitudes recientes, y la generación y envío de un nuevo PIN.

#### Métodos Principales de reenvío de PIN de recuperación

##### resend_recovery

::: app.user.application.password_recovery_process.resend_recovery_use_case.ResendRecoveryUseCase.resend_recovery

### Caso de Uso: Restablecimiento de Contraseña

::: app.user.application.password_recovery_process.reset_password_use_case.ResetPasswordUseCase

Este caso de uso maneja el proceso de restablecimiento de contraseña, incluyendo la validación del estado del usuario, la verificación del PIN de recuperación, y la actualización de la contraseña en la base de datos.

#### Métodos Principales de restablecimiento de contraseña

##### reset_password

::: app.user.application.password_recovery_process.reset_password_use_case.ResetPasswordUseCase.reset_password

## Otros Casos de Uso

### Caso de Uso: Cierre de Sesión

::: app.user.application.logout_use_case.LogoutUseCase

Este caso de uso maneja el proceso de cerrar sesión, incluyendo la inclusión del token en la lista negra.

#### Métodos Principales de cierre de sesión

##### logout

::: app.user.application.logout_use_case.LogoutUseCase.logout

### Caso de Uso: Obtener Usuario Actual

::: app.user.application.get_current_user_use_case.GetCurrentUserUseCase

Este caso de uso maneja la lógica para recuperar y validar la información del usuario actual.

#### Métodos Principales de obtener usuario actual

##### get_current_user

::: app.user.application.get_current_user_use_case.GetCurrentUserUseCase.get_current_user

### Caso de Uso: Actualizar Información de Usuario

::: app.user.application.update_user_info_use_case.UpdateUserInfoUseCase

Este caso de uso maneja el proceso de actualización de la información del usuario, incluyendo la verificación de correo electrónico duplicado.

#### Métodos Principales de actualización de información de usuario

##### update_user_info

::: app.user.application.update_user_info_use_case.UpdateUserInfoUseCase.update_user_info
