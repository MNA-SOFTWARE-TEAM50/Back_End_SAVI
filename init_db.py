"""
Script para inicializar la base de datos con datos de prueba
"""
from db.session import SessionLocal, sync_engine
from db.base import Base
from models.user import User
from models.product import Product
from models.customer import Customer
from core.security import get_password_hash
import uuid


def init_db():
    """Inicializar base de datos"""
    print("🔄 Creando tablas en MySQL...")
    Base.metadata.create_all(bind=sync_engine)
    
    db = SessionLocal()
    
    try:
        # Verificar si ya existen datos
        existing_user = db.query(User).first()
        if existing_user:
            print("⚠️  La base de datos ya tiene datos. Eliminando...")
            # Eliminar datos existentes
            db.query(User).delete()
            db.query(Product).delete()
            db.query(Customer).delete()
            db.commit()
            print("✅ Datos eliminados")
        
        print("📝 Creando datos de prueba...")
        
        # Generar UUIDs para usuarios
        admin_uuid = str(uuid.uuid4())
        cashier_uuid = str(uuid.uuid4())
        
        # Crear usuario admin
        admin_user = User(
            id=admin_uuid,
            username="admin",
            email="admin@savi.com",
            full_name="Administrador SAVI",
            hashed_password=get_password_hash("admin123"),
            role="admin",
            is_active=True
        )
        db.add(admin_user)
        
        # Crear usuario cajero
        cashier_user = User(
            id=cashier_uuid,
            username="cajero",
            email="cajero@savi.com",
            full_name="Cajero SAVI",
            hashed_password=get_password_hash("cajero123"),
            role="cashier",
            is_active=True
        )
        db.add(cashier_user)
        
        # Crear productos de ejemplo
        products = [
            Product(
                name="Coca Cola 600ml",
                description="Refresco de cola",
                price=15.50,
                stock=100,
                category="Bebidas",
                barcode="7501234567890"
            ),
            Product(
                name="Pan Blanco",
                description="Pan de caja blanco",
                price=35.00,
                stock=50,
                category="Panadería",
                barcode="7501234567891"
            ),
            Product(
                name="Leche Entera 1L",
                description="Leche fresca entera",
                price=25.00,
                stock=75,
                category="Lácteos",
                barcode="7501234567892"
            ),
            Product(
                name="Huevos 12 pzas",
                description="Docena de huevos",
                price=45.00,
                stock=30,
                category="Lácteos",
                barcode="7501234567893"
            ),
            Product(
                name="Papel Higiénico 4 rollos",
                description="Papel higiénico suave",
                price=55.00,
                stock=80,
                category="Higiene",
                barcode="7501234567894"
            ),
        ]
        
        for product in products:
            db.add(product)
        
        # Crear clientes de ejemplo
        customers = [
            Customer(
                name="Juan Pérez",
                email="juan.perez@example.com",
                phone="5551234567",
                address="Calle Principal 123"
            ),
            Customer(
                name="María García",
                email="maria.garcia@example.com",
                phone="5557654321",
                address="Avenida Central 456"
            ),
            Customer(
                name="Carlos López",
                email="carlos.lopez@example.com",
                phone="5559876543",
                address="Boulevard Norte 789"
            ),
        ]
        
        for customer in customers:
            db.add(customer)
        
        db.commit()
        print("\n✅ Base de datos inicializada correctamente!")
        print("\n📝 Usuarios creados:")
        print("   - Usuario: admin | Contraseña: admin123 | Rol: admin")
        print("   - Usuario: cajero | Contraseña: cajero123 | Rol: cashier")
        print("\n📦 5 productos creados")
        print("👥 3 clientes creados")
        print("\n🚀 Puedes iniciar el servidor con: uvicorn app.main:app --reload")
        
    except Exception as e:
        print(f"❌ Error al inicializar la base de datos: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("  SAVI - Inicialización de Base de Datos MySQL")
    print("=" * 60)
    init_db()
