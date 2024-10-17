# Modelos de Usuario

Este documento describe los modelos Pydantic utilizados para la gestión de usuarios en el sistema AgroInsight.

## Esquemas de Solicitud y Respuesta

### Crear Usuario

::: app.user.domain.schemas.UserCreate

### Reenvío de PIN de Confirmación

::: app.user.domain.schemas.ResendPinConfirmRequest

### Confirmación de Registro

::: app.user.domain.schemas.ConfirmationRequest

### Inicio de Sesión

::: app.user.domain.schemas.LoginRequest

### Reenvío de PIN de Autenticación de Dos Factores

::: app.user.domain.schemas.Resend2FARequest

### Verificación de Inicio de Sesión con Dos Factores

::: app.user.domain.schemas.TwoFactorAuthRequest

### Respuesta de Token

::: app.user.domain.schemas.TokenResponse

### Respuesta de Usuario

::: app.user.domain.schemas.UserResponse

### Actualizar Información de Usuario

::: app.user.domain.schemas.UserUpdate

### Recuperación de Contraseña

::: app.user.domain.schemas.PasswordRecoveryRequest

### Confirmación de PIN de Recuperación

::: app.user.domain.schemas.PinConfirmationRequest

### Restablecer Contraseña

::: app.user.domain.schemas.PasswordResetRequest

### Usuario en la Base de Datos

::: app.user.domain.schemas.UserInDB
