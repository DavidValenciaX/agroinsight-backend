# Visión General del Módulo de Medidas

## Introducción

El módulo de Medidas es un componente fundamental del sistema AgroInsight que gestiona todas las unidades de medida utilizadas en la plataforma. Este módulo proporciona una base estandarizada para el manejo de diferentes tipos de mediciones en agricultura, desde longitudes y áreas hasta densidades de siembra y rendimientos.

## Características Principales

### 1. Gestión de Unidades de Medida

- Categorización de unidades (longitud, área, volumen, etc.)
- Soporte para múltiples sistemas de medición
- Conversión entre unidades
- Estandarización de medidas en todo el sistema

### 2. Categorías de Unidades

- Longitud (metros, kilómetros, etc.)
- Área (hectáreas, metros cuadrados, etc.)
- Volumen (litros, metros cúbicos, etc.)
- Masa (kilogramos, toneladas, etc.)
- Tiempo (horas, días, etc.)
- Temperatura (Celsius, Fahrenheit)
- Densidad de siembra (plantas por hectárea)
- Moneda (diferentes divisas)
- Rendimiento (toneladas por hectárea)
- Presión (hectopascales)
- Porcentaje
- Velocidad (metros por segundo)
- Ángulo (grados)
- Tasa de precipitación (mm/hora)

### 3. Funcionalidades

- Listado de unidades disponibles
- Validación de unidades por categoría
- Gestión de abreviaturas estandarizadas
- Soporte multilingüe para nombres de unidades

## Integración con Otros Módulos

El módulo de Medidas se integra con:

- **Módulo de Cultivos**: Para medidas de rendimiento y densidad de siembra
- **Módulo de Lotes**: Para medidas de área y distancias
- **Módulo de Costos**: Para unidades monetarias
- **Módulo de Prácticas Culturales**: Para medidas de aplicación y dosificación

## Estructura Técnica

El módulo sigue una arquitectura limpia con:

- **Domain**: Definición de esquemas y reglas de negocio
- **Application**: Casos de uso y servicios
- **Infrastructure**: Implementación de repositorios y API
