"""
Script para eliminar todas las tablas y recrearlas con UUID
"""
from db.session import sync_engine
from db.base import Base

print("=" * 60)
print("  SAVI - Eliminando tablas existentes")
print("=" * 60)
print()

try:
    print("🗑️  Eliminando todas las tablas...")
    Base.metadata.drop_all(bind=sync_engine)
    print("✅ Tablas eliminadas correctamente")
    print()
    print("Ahora ejecuta: python init_db.py")
    print()
except Exception as e:
    print(f"❌ Error: {e}")
