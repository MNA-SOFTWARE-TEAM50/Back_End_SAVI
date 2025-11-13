# Cambios en el Sistema de Alertas de Inventario

## Fecha: 13 de Noviembre de 2025

## Resumen de Cambios

Se modificó la lógica de generación de alertas para que **siempre se creen nuevas alertas** en lugar de actualizar las existentes. Las alertas antiguas se desactivan automáticamente antes de crear las nuevas.

---

## Comportamiento Anterior ❌

Antes, el sistema verificaba si ya existía una alerta activa del mismo tipo para un producto:
- Si existía → se actualizaba la alerta existente
- Si no existía → se creaba una nueva alerta

**Problema:** No se podía ver el historial de alertas ya que siempre se actualizaba la misma.

---

## Comportamiento Actual ✅

Ahora, cada vez que se generan alertas:

1. **Se desactivan TODAS las alertas antiguas** del producto (de cualquier tipo)
   - Se marcan como `is_active = False`
   - Se registra la fecha de resolución (`resolved_at`)

2. **Se crean nuevas alertas** según las condiciones actuales del inventario
   - Siempre se crea una alerta nueva
   - No importa si ya existía una similar
   - Cada alerta tiene su propia fecha de creación

**Ventaja:** Se mantiene un historial completo de todas las alertas generadas.

---

## Cambios Técnicos en el Código

### Archivo: `api/v1/inventory_alerts.py`

#### Función: `generate_alerts()`

**Antes:**
```python
# Se obtenían alertas existentes del producto
existing_stock_alerts = ...

# Se verificaba si crear o actualizar
should_create_stock_alert = True
for alert in existing_stock_alerts:
    if alert.alert_type == 'no_stock':
        # Ya existe, actualizar
        alert.current_stock = 0
        should_create_stock_alert = False

# Solo crear si no existe
if should_create_stock_alert:
    alert = InventoryAlert(...)
    db.add(alert)
```

**Ahora:**
```python
# Se desactivan TODAS las alertas antiguas
old_alerts_result = await db.execute(
    select(InventoryAlert).where(
        and_(
            InventoryAlert.product_id == product.id,
            InventoryAlert.is_active == True
        )
    )
)
old_alerts = old_alerts_result.scalars().all()
for old_alert in old_alerts:
    old_alert.is_active = False
    old_alert.resolved_at = datetime.now()

# Siempre crear nueva alerta
if product.stock == 0:
    alert = InventoryAlert(...)
    db.add(alert)
```

---

## Impacto en el Sistema

### Base de Datos
- ✅ Se mantienen todas las alertas históricas (no se eliminan)
- ✅ Las alertas antiguas se marcan como inactivas
- ✅ Se puede auditar el historial completo de alertas

### Frontend
- ✅ Solo se muestran las alertas activas (`is_active = True`)
- ✅ Las estadísticas reflejan solo alertas activas
- ✅ El comportamiento visual es el mismo

### API
- ✅ Endpoint `/api/v1/inventory-alerts/` por defecto devuelve solo activas
- ✅ Endpoint `/api/v1/inventory-alerts/stats` cuenta solo activas
- ✅ Se puede consultar historial cambiando `active_only=false`

---

## Resultados de Pruebas

### Test Ejecutado: `test_duplicate_alerts.py`

```
Alertas iniciales: 3
Después de 1ra generación: 3 (nuevas)
Después de 2da generación: 3 (nuevas)

Total en BD: 32 (3 activas + 29 históricas)
```

✅ **Conclusión:** El sistema crea correctamente nuevas alertas en cada generación y mantiene el historial.

---

## Consultas Útiles

### Ver solo alertas activas (comportamiento por defecto)
```
GET /api/v1/inventory-alerts/?active_only=true
```

### Ver historial completo de alertas
```
GET /api/v1/inventory-alerts/?active_only=false&limit=500
```

### Ver alertas de un producto específico (incluyendo historial)
```sql
SELECT * FROM inventory_alerts 
WHERE product_id = 3 
ORDER BY created_at DESC;
```

---

## Mantenimiento

### Limpieza de Alertas Antiguas (Opcional)

Si en el futuro se desea eliminar alertas antiguas de la base de datos:

```python
# Eliminar alertas inactivas de hace más de 90 días
cutoff_date = datetime.now() - timedelta(days=90)
await db.execute(
    delete(InventoryAlert).where(
        and_(
            InventoryAlert.is_active == False,
            InventoryAlert.resolved_at < cutoff_date
        )
    )
)
```

---

## Archivos Modificados

- ✅ `Back_End_SAVI/api/v1/inventory_alerts.py` (función `generate_alerts`)
- ✅ `Back_End_SAVI/test_duplicate_alerts.py` (nuevo archivo de pruebas)

---

## Próximos Pasos Sugeridos

1. ✅ **Implementado:** Sistema de duplicados funcional
2. 🔄 **Opcional:** Agregar un job automático para limpiar alertas antiguas
3. 🔄 **Opcional:** Dashboard de historial de alertas en el frontend
4. 🔄 **Opcional:** Reportes de tendencias de alertas por producto

---

**Autor:** GitHub Copilot  
**Fecha:** 13 de Noviembre de 2025
