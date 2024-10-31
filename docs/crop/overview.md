# Visión General del Módulo de Cultivos

## Introducción

El módulo de cultivos de AgroInsight gestiona toda la información relacionada con los cultivos de maíz en las diferentes fincas. Este módulo es fundamental para el seguimiento y control de la producción agrícola.

## Características Principales

### 1. Gestión de Cultivos

- Creación y seguimiento de cultivos
- Registro de fechas de siembra y cosecha
- Control de densidad de siembra
- Seguimiento del estado del cultivo

### 2. Variedades de Maíz

- Catálogo de variedades disponibles
- Información detallada de cada variedad
- Recomendaciones de uso según la región

### 3. Estados del Cultivo

- Programado
- Sembrado
- Germinando
- Creciendo
- Floración
- Maduración
- Cosechado
- Enfermo
- Muerto
- Dormante

### 4. Métricas y Seguimiento

- Registro de producción total
- Control de ventas y precios
- Cálculo de rendimientos
- Análisis de costos e ingresos

## Integración con Otros Módulos

El módulo de cultivos se integra estrechamente con:

- Módulo de Lotes: Para la gestión de ubicaciones de cultivos
- Módulo de Prácticas Culturales: Para el seguimiento de labores agrícolas
- Módulo de Fincas: Para la administración general de la producción

## Casos de Uso Comunes

1. Registro de nuevo cultivo
2. Actualización de estado del cultivo
3. Registro de cosecha
4. Consulta de variedades disponibles
5. Generación de reportes de producción

## Estructura Técnica

El módulo sigue una arquitectura limpia con las siguientes capas:

- **Domain**: Modelos y reglas de negocio
- **Application**: Casos de uso y servicios
- **Infrastructure**: Implementaciones técnicas y acceso a datos

## Documentación Relacionada

- [Endpoints de Cultivos](endpoints.md)
- [Modelos de Datos](models.md)
- [Casos de Uso](use_cases.md)
