# Documentación del Endpoint de Reportes Financieros

## Descripción General

El endpoint de reportes financieros permite generar informes detallados sobre los costos, ingresos y ganancias de una finca agrícola. Este sistema permite filtrar y agrupar la información de diferentes maneras para obtener análisis específicos.

## Endpoint

`GET /reports/financial`

## Parámetros de la Solicitud

### Parámetros Obligatorios

- `farm_id` (int): ID de la finca para la cual se generará el reporte
- `start_date` (date): Fecha de inicio del período (formato: YYYY-MM-DD)
- `end_date` (date): Fecha fin del período (formato: YYYY-MM-DD)

### Parámetros Opcionales de Filtrado

- `plot_id` (int): Filtra los resultados para un lote específico
- `crop_id` (int): Filtra los resultados para un cultivo específico
- `min_cost` (float): Muestra solo las tareas con costo total mayor o igual a este valor
- `max_cost` (float): Muestra solo las tareas con costo total menor o igual a este valor
- `task_types` (List[str]): Lista de tipos de tareas específicas a incluir
- `only_profitable` (bool): Si es True, solo muestra elementos con ganancia positiva
- `currency` (str): Símbolo de la moneda en la que se desea el reporte (ej: COP, USD, EUR). Si no se especifica, se usa COP.

### Parámetros de Agrupación

- `group_by` (enum): Define cómo se agruparán los datos en el reporte
  - `"none"`: Sin agrupación (por defecto)
  - `"task_type"`: Agrupa las tareas por tipo
  - `"month"`: Agrupa las tareas por mes
  - `"cost_type"`: Agrupa los costos por categoría (Mano de obra, Insumos, Maquinaria)

## Estructura del Reporte

El reporte se organiza jerárquicamente:

1. **Nivel Finca**
   - Información general de la finca
   - Totales globales (costos, ingresos, ganancias)
   - Moneda utilizada
   - Top 10 de maquinaria más utilizada
   - Top 10 de insumos más utilizados

2. **Nivel Lote**
   - Información de cada lote
   - Costos de mantenimiento base
   - Tareas específicas del lote
   - Subtotales por lote

3. **Nivel Cultivo**
   - Información de cultivos por lote
   - Datos de producción y ventas
   - Tareas específicas del cultivo
   - Costos e ingresos por cultivo

## Cálculo de Costos

El sistema calcula tres tipos principales de costos:

1. **Costos de Mano de Obra**: Gastos relacionados con el trabajo humano
2. **Costos de Insumos**: Gastos en materiales y productos
3. **Costos de Maquinaria**: Gastos relacionados con equipos y maquinaria

## Funcionalidades de Agrupación

### Agrupación por Tipo de Tarea

- Combina todas las tareas del mismo tipo
- Suma los costos por categoría
- Útil para analizar qué tipos de tareas son más costosas

### Agrupación por Mes

- Organiza las tareas por mes de ejecución
- Permite ver la distribución temporal de gastos
- Facilita el análisis de estacionalidad

### Agrupación por Tipo de Costo

- Consolida los gastos en las tres categorías principales
- Permite ver la distribución del presupuesto
- Útil para análisis de estructura de costos

## Seguridad y Permisos

- Requiere autenticación mediante JWT
- Verifica que el usuario sea administrador de la finca
- Registra la actividad en los logs del sistema

## Ejemplo de Uso

```http
GET /reports/financial?farm_id=1&start_date=2024-01-01&end_date=2024-12-31&group_by=month&min_cost=100&only_profitable=true&currency=USD
```

Este ejemplo generaría un reporte:

- Para todo el año 2024
- Agrupado por meses
- Solo mostrando tareas con costo mayor a 100
- Incluyendo solo elementos rentables
- En moneda USD

## Consideraciones Técnicas

- Los cálculos monetarios se realizan usando el tipo Decimal para evitar errores de redondeo
- Las fechas se manejan en formato ISO (YYYY-MM-DD)
- Los resultados se devuelven en la moneda especificada por el parámetro `currency` (por defecto COP)
- El sistema realiza automáticamente la conversión de monedas según las tasas configuradas
- El sistema maneja automáticamente la conversión de tipos de datos

## Casos de Uso Comunes

1. **Análisis de Rentabilidad**

   ```http
   GET /reports/financial?farm_id=1&only_profitable=true
   ```

2. **Análisis de Costos por Tipo**

   ```http
   GET /reports/financial?farm_id=1&group_by=cost_type
   ```

3. **Análisis Mensual**

   ```http
   GET /reports/financial?farm_id=1&group_by=month
   ```

4. **Análisis de Lote Específico**

   ```http
   GET /reports/financial?farm_id=1&plot_id=5
   ```

## Estructura de la Respuesta

```json
{
    "finca_id": 1,
    "finca_nombre": "Finca Ejemplo",
    "fecha_inicio": "2024-01-01",
    "fecha_fin": "2024-12-31",
    "moneda_simbolo": "COP",
    "lotes": [
        {
            "lote_id": 1,
            "lote_nombre": "Lote A",
            "cultivos": [
                {
                    "cultivo_id": 1,
                    "variedad_maiz": "DK-7088",
                    "fecha_siembra": "2024-01-15",
                    "fecha_cosecha": "2024-05-15",
                    "produccion_total": 5000,
                    "cantidad_vendida": 4800,
                    "precio_venta_unitario": 2500,
                    "ingreso_total": 12000000,
                    "costo_produccion": 8000000,
                    "tareas_cultivo": [...],
                    "costo_total": 9000000,
                    "ganancia_neta": 3000000
                }
            ],
            "tareas_lote": [...],
            "costo_mantenimiento_base": 1000000,
            "costo_tareas": 2000000,
            "costo_cultivos": 9000000,
            "costo_total": 12000000,
            "ingreso_total": 12000000,
            "ganancia_neta": 0
        }
    ],
    "top_maquinaria": [
        {
            "maquinaria_id": 1,
            "nombre": "John Deere 6110J",
            "tipo_maquinaria_nombre": "Tractor",
            "total_horas_uso": 120,
            "costo_total": "6000000.00"
        }
    ],
    "top_insumos": [
        {
            "insumo_id": 1,
            "nombre": "Urea",
            "categoria_nombre": "Fertilizantes",
            "unidad_medida_simbolo": "kg",
            "cantidad_total": 500,
            "costo_total": "1250000.00"
        }
    ],
    "costo_total": "12000000.00",
    "ingreso_total": "15000000.00",
    "ganancia_neta": "3000000.00"
}
```

## Códigos de Error

| Código HTTP | Descripción | Causa |
|------------|-------------|-------|
| 403 | Forbidden | El usuario no tiene permisos de administrador en la finca |
| 404 | Not Found | La finca especificada no existe |
| 500 | Internal Server Error | Error al obtener la moneda por defecto u otros errores internos |

## Limitaciones y Consideraciones de Rendimiento

### Rango de Fechas

- Se recomienda no solicitar períodos mayores a 1 año para mantener tiempos de respuesta óptimos
- Para análisis de períodos más largos, considere hacer múltiples solicitudes

### Rendimiento

- El tiempo de respuesta aumenta con:
  - Número de lotes en la finca
  - Número de cultivos por lote
  - Cantidad de tareas en el período
  - Complejidad de la agrupación solicitada

### Recomendaciones

- Use filtros específicos cuando sea posible (plot_id, crop_id)
- Para análisis de grandes volúmenes de datos, considere usar la agrupación por mes
- Evite solicitar datos de múltiples lotes si solo necesita información específica

## Implementación en React Native (TypeScript)

### Tipos de Datos

```typescript
// types/reports.ts
export interface TaskCost {
  tarea_id: number;
  tarea_nombre: string;
  tipo_labor_nombre: string;
  nivel: 'LOTE' | 'CULTIVO' | 'AGRUPADO';
  fecha: string;
  costo_mano_obra: number;
  costo_insumos: number;
  costo_maquinaria: number;
  costo_total: number;
  observaciones?: string;
}

export interface CropFinancials {
  cultivo_id: number;
  variedad_maiz: string;
  fecha_siembra: string;
  fecha_cosecha: string;
  produccion_total: number;
  cantidad_vendida: number;
  precio_venta_unitario: number;
  ingreso_total: number;
  costo_produccion: number;
  tareas_cultivo: TaskCost[];
  costo_total: number;
  ganancia_neta: number;
}

export interface PlotFinancials {
  lote_id: number;
  lote_nombre: string;
  cultivos: CropFinancials[];
  tareas_lote: TaskCost[];
  costo_mantenimiento_base: number;
  costo_tareas: number;
  costo_cultivos: number;
  costo_total: number;
  ingreso_total: number;
  ganancia_neta: number;
}

export interface FarmFinancialReport {
  finca_id: number;
  finca_nombre: string;
  fecha_inicio: string;
  fecha_fin: string;
  moneda: string;
  lotes: PlotFinancials[];
  costo_total: number;
  ingreso_total: number;
  ganancia_neta: number;
}
```

### Hook Personalizado para Reportes

```typescript
// hooks/useFinancialReport.ts
import { useState } from 'react';
import axios from 'axios';
import { FarmFinancialReport } from '../types/reports';

interface UseFinancialReportParams {
  farmId: number;
  startDate: string;
  endDate: string;
  plotId?: number;
  cropId?: number;
  minCost?: number;
  maxCost?: number;
  taskTypes?: string[];
  groupBy?: 'none' | 'task_type' | 'month' | 'cost_type';
  onlyProfitable?: boolean;
}

export const useFinancialReport = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<FarmFinancialReport | null>(null);

  const generateReport = async (params: UseFinancialReportParams) => {
    try {
      setLoading(true);
      setError(null);

      const queryParams = new URLSearchParams({
        farm_id: params.farmId.toString(),
        start_date: params.startDate,
        end_date: params.endDate,
        ...(params.plotId && { plot_id: params.plotId.toString() }),
        ...(params.cropId && { crop_id: params.cropId.toString() }),
        ...(params.minCost && { min_cost: params.minCost.toString() }),
        ...(params.maxCost && { max_cost: params.maxCost.toString() }),
        ...(params.groupBy && { group_by: params.groupBy }),
        ...(params.onlyProfitable !== undefined && { 
          only_profitable: params.onlyProfitable.toString() 
        }),
      });

      // Agregar task_types como parámetros múltiples si existen
      params.taskTypes?.forEach(type => {
        queryParams.append('task_types', type);
      });

      const response = await axios.get<FarmFinancialReport>(
        `/reports/financial?${queryParams.toString()}`,
        {
          headers: {
            Authorization: `Bearer ${await getToken()}` // Función para obtener el token JWT
          }
        }
      );

      setReport(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al generar el reporte');
    } finally {
      setLoading(false);
    }
  };

  return { generateReport, report, loading, error };
};
```

### Ejemplo de Uso en Componente

```typescript
// screens/FinancialReportScreen.tsx
import React, { useState } from 'react';
import { View, Text, ActivityIndicator } from 'react-native';
import { useFinancialReport } from '../hooks/useFinancialReport';
import DatePicker from '../components/DatePicker';
import { Button } from '../components/Button';

export const FinancialReportScreen: React.FC = () => {
  const [startDate, setStartDate] = useState(new Date());
  const [endDate, setEndDate] = useState(new Date());
  const { generateReport, report, loading, error } = useFinancialReport();

  const handleGenerateReport = async () => {
    await generateReport({
      farmId: 1, // ID de la finca actual
      startDate: startDate.toISOString().split('T')[0],
      endDate: endDate.toISOString().split('T')[0],
      groupBy: 'month',
      onlyProfitable: true,
      minCost: 100
    });
  };

  if (loading) {
    return <ActivityIndicator size="large" />;
  }

  if (error) {
    return <Text style={styles.error}>{error}</Text>;
  }

  return (
    <View style={styles.container}>
      <DatePicker
        label="Fecha Inicio"
        value={startDate}
        onChange={setStartDate}
      />
      <DatePicker
        label="Fecha Fin"
        value={endDate}
        onChange={setEndDate}
      />
      <Button 
        title="Generar Reporte" 
        onPress={handleGenerateReport} 
      />
      
      {report && (
        <View style={styles.reportContainer}>
          <Text style={styles.title}>
            Reporte: {report.finca_nombre}
          </Text>
          <Text style={styles.summary}>
            Costo Total: {report.costo_total}
          </Text>
          <Text style={styles.summary}>
            Ingreso Total: {report.ingreso_total}
          </Text>
          <Text style={styles.profit}>
            Ganancia Neta: {report.ganancia_neta}
          </Text>
          
          {/* Renderizar detalles de lotes */}
          {report.lotes.map(plot => (
            <View key={plot.lote_id} style={styles.plotContainer}>
              <Text style={styles.plotTitle}>
                {plot.lote_nombre}
              </Text>
              <Text>
                Ganancia: {plot.ganancia_neta}
              </Text>
              {/* ... más detalles del lote ... */}
            </View>
          ))}
        </View>
      )}
    </View>
  );
};

const styles = {
  container: {
    flex: 1,
    padding: 16,
  },
  error: {
    color: 'red',
    textAlign: 'center',
  },
  reportContainer: {
    marginTop: 20,
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
  },
  summary: {
    fontSize: 16,
    marginTop: 8,
  },
  profit: {
    fontSize: 18,
    fontWeight: 'bold',
    marginTop: 8,
  },
  plotContainer: {
    marginTop: 16,
    padding: 12,
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
  },
  plotTitle: {
    fontSize: 16,
    fontWeight: 'bold',
  },
};
```

Este ejemplo incluye:

- Definición completa de tipos TypeScript
- Hook personalizado para manejar la lógica del reporte
- Componente de ejemplo con gestión de estados y errores
- Manejo de fechas y parámetros opcionales
- Estilos básicos para la visualización
- Integración con sistema de autenticación JWT

Los componentes `DatePicker` y `Button` son componentes personalizados que deberás implementar según tu UI Kit específico (por ejemplo, usando React Native Paper, Native Base, etc.).
