# Sistema de Alertas de Inventario - SAVI

## 📋 Descripción

El sistema de alertas de inventario proporciona monitoreo automático del estado del inventario y notifica sobre situaciones que requieren atención, como:

- 🔴 **Stock agotado** - Productos sin existencias
- 🟠 **Stock bajo** - Productos que necesitan reabastecimiento
- 🟡 **Sin movimiento** - Productos que no se han vendido en un período
- 🔵 **Sugerencias de reabastecimiento** - Análisis predictivo

## 🚀 Instalación

### 1. Ejecutar migración de base de datos

```bash
cd Back_End_SAVI
python db/upgrade_inventory_alerts.py
```

### 2. Reiniciar el servidor

```bash
uvicorn main:app --reload
```

## 📡 Endpoints de la API

### Estadísticas de Alertas

**GET** `/api/v1/inventory-alerts/stats`

Obtiene estadísticas generales de las alertas.

**Respuesta:**
```json
{
  "total_alerts": 45,
  "active_alerts": 23,
  "unread_alerts": 15,
  "critical_alerts": 5,
  "by_type": {
    "low_stock": 12,
    "no_stock": 5,
    "no_movement": 6
  },
  "by_severity": {
    "critical": 5,
    "high": 8,
    "medium": 7,
    "low": 3
  }
}
```

---

### Listar Alertas

**GET** `/api/v1/inventory-alerts/`

Lista todas las alertas con filtros opcionales.

**Parámetros:**
- `skip` (int): Paginación - Elementos a saltar (default: 0)
- `limit` (int): Paginación - Límite de resultados (default: 100, max: 500)
- `active_only` (bool): Solo alertas activas (default: true)
- `unread_only` (bool): Solo alertas no leídas (default: false)
- `alert_type` (string): Filtrar por tipo (low_stock, no_stock, no_movement, restock_suggestion)
- `severity` (string): Filtrar por severidad (low, medium, high, critical)

**Respuesta:**
```json
[
  {
    "id": 1,
    "product_id": 5,
    "product_name": "Laptop Dell XPS 13",
    "product_sku": "LAP-001",
    "product_category": "Electrónica",
    "alert_type": "low_stock",
    "severity": "critical",
    "message": "El producto 'Laptop Dell XPS 13' tiene stock crítico (3 unidades).",
    "current_stock": 3,
    "threshold": 5,
    "is_active": true,
    "is_read": false,
    "created_at": "2025-11-13T10:30:00",
    "updated_at": null,
    "resolved_at": null
  }
]
```

---

### Obtener Alerta por ID

**GET** `/api/v1/inventory-alerts/{alert_id}`

Obtiene detalles de una alerta específica.

**Respuesta:** Objeto de alerta con información del producto.

---

### Generar Alertas Automáticamente

**POST** `/api/v1/inventory-alerts/generate`

Genera alertas automáticas basadas en el estado actual del inventario.

**Requiere:** Rol de `admin` o `manager`

**Body (opcional):**
```json
{
  "low_stock_threshold": 10,
  "critical_stock_threshold": 5,
  "no_movement_days": 30,
  "auto_generate_alerts": true
}
```

**Respuesta:**
```json
{
  "message": "Se generaron 15 alertas",
  "alerts": [
    "Sin stock: Mouse Inalámbrico",
    "Stock crítico: Teclado Mecánico (2)",
    "Stock bajo: Monitor 24\" (8)",
    "Sin movimiento: Cable HDMI 2m"
  ]
}
```

---

### Marcar Alerta como Leída

**POST** `/api/v1/inventory-alerts/{alert_id}/mark-read`

Marca una alerta como leída.

**Respuesta:**
```json
{
  "message": "Alerta marcada como leída",
  "alert_id": 1
}
```

---

### Resolver Alerta

**POST** `/api/v1/inventory-alerts/{alert_id}/resolve`

Marca una alerta como resuelta (inactiva).

**Respuesta:**
```json
{
  "message": "Alerta resuelta",
  "alert_id": 1
}
```

---

### Marcar Todas como Leídas

**POST** `/api/v1/inventory-alerts/mark-all-read`

Marca todas las alertas activas como leídas.

**Respuesta:**
```json
{
  "message": "15 alertas marcadas como leídas"
}
```

---

### Actualizar Alerta

**PATCH** `/api/v1/inventory-alerts/{alert_id}`

Actualiza el estado de una alerta.

**Body:**
```json
{
  "is_read": true,
  "is_active": false
}
```

---

### Eliminar Alerta

**DELETE** `/api/v1/inventory-alerts/{alert_id}`

Elimina una alerta permanentemente.

**Requiere:** Rol de `admin`

## 🎯 Tipos de Alertas

### 1. Sin Stock (no_stock)
- **Severidad:** Critical
- **Trigger:** Stock = 0
- **Acción:** Reabastecimiento urgente necesario

### 2. Stock Bajo (low_stock)
- **Severidad:** Critical (≤ threshold crítico) o High (≤ threshold bajo)
- **Trigger:** Stock por debajo del umbral configurado
- **Acción:** Planificar reabastecimiento

### 3. Sin Movimiento (no_movement)
- **Severidad:** Medium
- **Trigger:** No hay ventas en X días (configurable)
- **Acción:** Considerar promociones o descuentos

### 4. Sugerencia de Reabastecimiento (restock_suggestion)
- **Severidad:** Low
- **Trigger:** Análisis de patrones de venta
- **Acción:** Revisar necesidades de inventario

## ⚙️ Configuración

### Umbrales Predeterminados

```python
{
  "low_stock_threshold": 10,        # Stock mínimo antes de alerta
  "critical_stock_threshold": 5,    # Stock crítico
  "no_movement_days": 30,           # Días sin ventas para alerta
  "auto_generate_alerts": true      # Generar alertas automáticamente
}
```

### Personalización

Puedes ajustar los umbrales al llamar el endpoint de generación:

```bash
curl -X POST "http://localhost:8000/api/v1/inventory-alerts/generate" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "low_stock_threshold": 15,
    "critical_stock_threshold": 8,
    "no_movement_days": 45
  }'
```

## 🔄 Uso Recomendado

### 1. Generación Automática (Cron/Scheduled Task)

Configura una tarea programada para generar alertas periódicamente:

```bash
# Linux/Mac (crontab)
0 6 * * * cd /path/to/Back_End_SAVI && python -c "import requests; requests.post('http://localhost:8000/api/v1/inventory-alerts/generate', headers={'Authorization': 'Bearer TOKEN'})"

# Windows (Task Scheduler)
# Crear tarea que ejecute el script de generación diariamente
```

### 2. Integración en el Frontend

```typescript
// Obtener alertas no leídas
const getUnreadAlerts = async () => {
  const response = await fetch('/api/v1/inventory-alerts/?unread_only=true', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return await response.json();
};

// Generar alertas
const generateAlerts = async () => {
  const response = await fetch('/api/v1/inventory-alerts/generate', {
    method: 'POST',
    headers: { 
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      low_stock_threshold: 10,
      critical_stock_threshold: 5,
      no_movement_days: 30
    })
  });
  return await response.json();
};
```

### 3. Notificaciones en Tiempo Real

Consulta las estadísticas para mostrar un badge de notificaciones:

```typescript
const stats = await fetch('/api/v1/inventory-alerts/stats');
const { unread_alerts } = await stats.json();

// Mostrar badge con número de alertas no leídas
<Badge count={unread_alerts} />
```

## 🧪 Pruebas

Ejecuta el script de pruebas incluido:

```bash
# Asegúrate de que el servidor esté corriendo
uvicorn main:app --reload

# En otra terminal
python test_inventory_alerts.py
```

## 📊 Flujo de Trabajo

```
1. [Generación] → Se ejecuta generación automática o manual
                 ↓
2. [Análisis]   → Sistema analiza inventario actual
                 ↓
3. [Creación]   → Se crean alertas según umbrales
                 ↓
4. [Notificación] → Frontend muestra alertas al usuario
                 ↓
5. [Acción]     → Usuario marca como leída o resuelve
                 ↓
6. [Resolución] → Alerta se marca como inactiva
```

## 🔐 Permisos

- **Listar/Ver alertas:** Todos los usuarios autenticados
- **Marcar como leída:** Todos los usuarios autenticados
- **Generar alertas:** `admin` o `manager`
- **Eliminar alertas:** Solo `admin`

## 💡 Ejemplos de Uso

### Dashboard con Alertas Críticas

```python
# Obtener solo alertas críticas activas
critical_alerts = requests.get(
    f"{BASE_URL}/inventory-alerts/",
    headers={"Authorization": f"Bearer {token}"},
    params={
        "severity": "critical",
        "active_only": True,
        "limit": 5
    }
)
```

### Widget de Notificaciones

```python
# Obtener estadísticas para widget
stats = requests.get(
    f"{BASE_URL}/inventory-alerts/stats",
    headers={"Authorization": f"Bearer {token}"}
)

# Mostrar: "Tienes 5 alertas críticas sin leer"
```

### Reporte de Productos Sin Movimiento

```python
# Filtrar alertas de productos sin movimiento
no_movement = requests.get(
    f"{BASE_URL}/inventory-alerts/",
    headers={"Authorization": f"Bearer {token}"},
    params={
        "alert_type": "no_movement",
        "active_only": True
    }
)
```

## 🚨 Troubleshooting

### Las alertas no se generan

1. Verifica que la tabla existe: `python db/upgrade_inventory_alerts.py`
2. Confirma permisos del usuario (admin o manager)
3. Revisa logs del servidor

### Alertas duplicadas

El sistema desactiva automáticamente alertas antiguas del mismo producto antes de crear nuevas.

### Performance con muchas alertas

- Usa paginación (`skip` y `limit`)
- Filtra por `active_only=true`
- Considera archivar alertas antiguas periódicamente

## 📈 Métricas Recomendadas

- Tiempo promedio de resolución de alertas
- Alertas críticas por día/semana
- Productos con alertas recurrentes
- Tasa de reabastecimiento vs alertas generadas

---

**¿Preguntas o sugerencias?**  
Contacta al equipo de desarrollo: A01795088@tec.mx
