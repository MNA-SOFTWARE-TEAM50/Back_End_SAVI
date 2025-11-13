"""
Script de migración para agregar tabla de alertas de inventario
"""
import sys
import os

# Agregar el directorio padre al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, inspect
from core.config import settings
from db.base import Base
from models.inventory_alert import InventoryAlert

def upgrade_inventory_alerts():
    """
    Crear tabla de alertas de inventario si no existe
    """
    # Crear engine síncrono
    engine = create_engine(settings.DATABASE_URL.replace('aiomysql', 'pymysql'))
    inspector = inspect(engine)
    
    # Verificar si la tabla ya existe
    if 'inventory_alerts' in inspector.get_table_names():
        print("✓ La tabla 'inventory_alerts' ya existe")
        return
    
    print("Creando tabla 'inventory_alerts'...")
    
    # Crear solo la tabla de alertas
    InventoryAlert.__table__.create(bind=engine, checkfirst=True)
    
    print("✓ Tabla 'inventory_alerts' creada exitosamente")
    print("\nEstructura de la tabla:")
    print("- id: INTEGER (Primary Key)")
    print("- product_id: INTEGER (Foreign Key -> products.id)")
    print("- alert_type: VARCHAR(50) - Tipo de alerta")
    print("- severity: VARCHAR(20) - Nivel de severidad")
    print("- message: TEXT - Mensaje descriptivo")
    print("- is_active: BOOLEAN - Si la alerta está activa")
    print("- is_read: BOOLEAN - Si fue leída")
    print("- resolved_at: DATETIME - Cuándo se resolvió")
    print("- current_stock: INTEGER - Stock actual al momento")
    print("- threshold: INTEGER - Umbral configurado")
    print("- days_without_movement: INTEGER - Días sin ventas")
    print("- created_at: DATETIME")
    print("- updated_at: DATETIME")

if __name__ == "__main__":
    print("=" * 60)
    print("MIGRACIÓN: Alertas de Inventario")
    print("=" * 60)
    
    try:
        upgrade_inventory_alerts()
        print("\n✓ Migración completada exitosamente")
    except Exception as e:
        print(f"\n✗ Error durante la migración: {str(e)}")
        sys.exit(1)
