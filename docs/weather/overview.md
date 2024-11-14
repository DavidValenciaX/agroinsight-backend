# Visión General del Módulo de Clima

## Introducción

El módulo de Clima es una parte esencial del sistema AgroInsight que proporciona información meteorológica en tiempo real y registros históricos para las fincas y lotes. Este módulo utiliza la API de OpenWeatherMap para obtener datos precisos y actualizados sobre las condiciones climáticas.

## Características Principales

### 1. Datos Meteorológicos en Tiempo Real

- Temperatura actual y sensación térmica
- Presión atmosférica
- Humedad relativa
- Precipitación
- Índice UV
- Nubosidad
- Velocidad y dirección del viento
- Visibilidad
- Punto de rocío

### 2. Registro Histórico

- Almacenamiento de datos meteorológicos por lote
- Seguimiento temporal de condiciones climáticas
- Consulta de registros por rango de fechas
- Análisis de tendencias climáticas

### 3. Integración con OpenWeatherMap

- Conexión en tiempo real con la API
- Datos en unidades métricas
- Descripciones detalladas del clima
- Códigos de condición meteorológica

### 4. Gestión de Unidades de Medida

- Soporte para múltiples unidades
- Conversión automática de unidades
- Validación de mediciones
- Integración con el módulo de medidas

## Integración con Otros Módulos

El módulo de Clima se integra con:

- **Módulo de Lotes**: Para asociar registros meteorológicos a ubicaciones específicas
- **Módulo de Medidas**: Para la gestión de unidades de medición
- **Módulo de Cultivos**: Para análisis de condiciones climáticas óptimas

## Casos de Uso Comunes

1. Consulta de clima actual para un lote
2. Registro automático de condiciones meteorológicas
3. Análisis de históricos climáticos
4. Verificación de conectividad con API externa
5. Gestión de registros meteorológicos

## Estructura Técnica

El módulo sigue una arquitectura limpia con:

- **Domain**: Definición de esquemas y reglas de negocio
- **Application**: Casos de uso y servicios
- **Infrastructure**: Implementación de repositorio y API
