"""
Script para agregar campos de promoción y descuento a la tabla products
"""
import sys
import os
import pymysql
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de base de datos desde DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+aiomysql://root:Mc4stroG+@localhost:3306/savidb")
# Parsear la URL: mysql+aiomysql://user:pass@host:port/dbname
import re
match = re.match(r'mysql\+aiomysql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', DATABASE_URL)
if match:
    DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME = match.groups()
    DB_PORT = int(DB_PORT)
else:
    DB_HOST = "localhost"
    DB_PORT = 3306
    DB_USER = "root"
    DB_PASSWORD = "Mc4stroG+"
    DB_NAME = "savidb"


def upgrade():
    """Agregar campos de promoción y descuento"""
    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    
    cursor = conn.cursor()
    
    try:
        # Agregar columna de descuento en porcentaje
        cursor.execute(
            "ALTER TABLE products ADD COLUMN discount_percentage FLOAT DEFAULT 0.0"
        )
        print("✅ Columna 'discount_percentage' agregada")
        
        # Agregar columna para activar/desactivar promoción
        cursor.execute(
            "ALTER TABLE products ADD COLUMN has_promotion BOOLEAN DEFAULT FALSE"
        )
        print("✅ Columna 'has_promotion' agregada")
        
        # Agregar columna para fecha de inicio de promoción
        cursor.execute(
            "ALTER TABLE products ADD COLUMN promotion_start DATETIME NULL"
        )
        print("✅ Columna 'promotion_start' agregada")
        
        # Agregar columna para fecha de fin de promoción
        cursor.execute(
            "ALTER TABLE products ADD COLUMN promotion_end DATETIME NULL"
        )
        print("✅ Columna 'promotion_end' agregada")
        
        # Agregar columna para descripción de promoción
        cursor.execute(
            "ALTER TABLE products ADD COLUMN promotion_description VARCHAR(500) NULL"
        )
        print("✅ Columna 'promotion_description' agregada")
        
        conn.commit()
        print("\n✅ Migración completada exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error durante la migración: {str(e)}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def downgrade():
    """Revertir cambios"""
    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE products DROP COLUMN discount_percentage")
        cursor.execute("ALTER TABLE products DROP COLUMN has_promotion")
        cursor.execute("ALTER TABLE products DROP COLUMN promotion_start")
        cursor.execute("ALTER TABLE products DROP COLUMN promotion_end")
        cursor.execute("ALTER TABLE products DROP COLUMN promotion_description")
        conn.commit()
        print("✅ Rollback completado")
        return True
    except Exception as e:
        print(f"❌ Error durante rollback: {str(e)}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    print("="*60)
    print("MIGRACIÓN: Agregar campos de promoción y descuento")
    print("="*60)
    
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        print("\n⚠️  Ejecutando DOWNGRADE (revertir cambios)...")
        downgrade()
    else:
        print("\n▶️  Ejecutando UPGRADE (aplicar cambios)...")
        upgrade()
