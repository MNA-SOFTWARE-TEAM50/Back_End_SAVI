"""
Test para verificar que el sistema de promociones funciona correctamente
"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/v1"

def login():
    """Autenticar y obtener token"""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={
            "username": "admin",
            "password": "admin123"
        }
    )
    return response.json()["access_token"]

def get_headers(token):
    """Obtener headers con token"""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

def test_promotions():
    """Test principal: verificar sistema de promociones"""
    print("\n" + "="*70)
    print("TEST: SISTEMA DE PROMOCIONES Y DESCUENTOS")
    print("="*70)
    
    # 1. Autenticarse
    print("\n1️⃣ Autenticando...")
    token = login()
    headers = get_headers(token)
    print("✅ Token obtenido")
    
    # 2. Obtener un producto existente
    print("\n2️⃣ Obteniendo lista de productos...")
    response = requests.get(f"{BASE_URL}/products?limit=5", headers=headers)
    products = response.json()
    
    if not products.get('items'):
        print("❌ No hay productos en la base de datos")
        return
    
    test_product = products['items'][0]
    product_id = test_product['id']
    print(f"✅ Producto seleccionado: {test_product['name']} (ID: {product_id})")
    print(f"   Precio original: ${test_product['price']}")
    
    # 3. Aplicar promoción al producto
    print(f"\n3️⃣ Aplicando promoción de 15% al producto...")
    
    now = datetime.now()
    start_date = now.isoformat()
    end_date = (now + timedelta(days=7)).isoformat()
    
    promotion_data = {
        "has_promotion": True,
        "discount_percentage": 15.0,
        "promotion_start": start_date,
        "promotion_end": end_date,
        "promotion_description": "Oferta de prueba automática"
    }
    
    response = requests.put(
        f"{BASE_URL}/products/{product_id}",
        headers=headers,
        json=promotion_data
    )
    
    if response.status_code == 200:
        updated = response.json()
        print("✅ Promoción aplicada exitosamente")
        print(f"\n📊 Detalles de la promoción:")
        print(f"   Producto: {updated['name']}")
        print(f"   Precio original: ${updated['price']}")
        print(f"   Descuento: {updated.get('discount_percentage', 0)}%")
        print(f"   Precio con descuento: ${updated['price'] * (1 - updated.get('discount_percentage', 0) / 100):.2f}")
        print(f"   Descripción: {updated.get('promotion_description', 'N/A')}")
        print(f"   Inicio: {updated.get('promotion_start', 'N/A')}")
        print(f"   Fin: {updated.get('promotion_end', 'N/A')}")
        print(f"   Activa: {'✅ Sí' if updated.get('has_promotion') else '❌ No'}")
    else:
        print(f"❌ Error al aplicar promoción: {response.status_code}")
        print(f"   Respuesta: {response.text}")
        return
    
    # 4. Verificar que la promoción se guardó correctamente
    print(f"\n4️⃣ Verificando que la promoción se guardó...")
    response = requests.get(f"{BASE_URL}/products/{product_id}", headers=headers)
    
    if response.status_code == 200:
        product = response.json()
        print("✅ Promoción verificada")
        print(f"   Promoción activa: {product.get('has_promotion')}")
        print(f"   Descuento: {product.get('discount_percentage')}%")
    else:
        print(f"❌ Error al verificar: {response.status_code}")
    
    # 5. Crear un nuevo producto CON promoción
    print(f"\n5️⃣ Creando nuevo producto con promoción...")
    
    new_product = {
        "name": "Producto Test con Promoción",
        "description": "Este producto fue creado para probar el sistema de promociones",
        "price": 100.0,
        "stock": 50,
        "category": "Test",
        "sku": f"TEST-PROMO-{datetime.now().timestamp()}",
        "barcode": f"BAR{datetime.now().timestamp()}",
        "has_promotion": True,
        "discount_percentage": 25.0,
        "promotion_description": "Lanzamiento especial - 25% OFF"
    }
    
    response = requests.post(
        f"{BASE_URL}/products",
        headers=headers,
        json=new_product
    )
    
    if response.status_code in [200, 201]:
        created = response.json()
        print("✅ Producto con promoción creado exitosamente")
        print(f"   ID: {created['id']}")
        print(f"   Nombre: {created['name']}")
        print(f"   Precio: ${created['price']}")
        print(f"   Descuento: {created.get('discount_percentage')}%")
        print(f"   Precio final: ${created['price'] * (1 - created.get('discount_percentage', 0) / 100):.2f}")
        
        # Limpiar: eliminar producto de prueba
        print(f"\n   🧹 Limpiando... eliminando producto de prueba")
        requests.delete(f"{BASE_URL}/products/{created['id']}", headers=headers)
        print(f"   ✅ Producto eliminado")
    else:
        print(f"❌ Error al crear producto: {response.status_code}")
        print(f"   Respuesta: {response.text}")
    
    # 6. Desactivar la promoción del primer producto
    print(f"\n6️⃣ Desactivando promoción del primer producto...")
    
    response = requests.put(
        f"{BASE_URL}/products/{product_id}",
        headers=headers,
        json={"has_promotion": False}
    )
    
    if response.status_code == 200:
        updated = response.json()
        print("✅ Promoción desactivada")
        print(f"   Promoción activa: {'✅ Sí' if updated.get('has_promotion') else '❌ No'}")
    else:
        print(f"❌ Error al desactivar: {response.status_code}")
    
    # 7. Listar productos con promoción activa
    print(f"\n7️⃣ Buscando productos con promoción activa...")
    response = requests.get(f"{BASE_URL}/products?limit=100", headers=headers)
    
    if response.status_code == 200:
        all_products = response.json()['items']
        products_with_promo = [p for p in all_products if p.get('has_promotion')]
        
        print(f"✅ Productos encontrados: {len(all_products)}")
        print(f"   Con promoción activa: {len(products_with_promo)}")
        
        if products_with_promo:
            print(f"\n   📋 Productos en promoción:")
            for p in products_with_promo[:5]:  # Mostrar máximo 5
                discount = p.get('discount_percentage', 0)
                original_price = p['price']
                final_price = original_price * (1 - discount / 100)
                print(f"\n   • {p['name']}")
                print(f"     Precio: ${original_price} → ${final_price:.2f} (-{discount}%)")
                if p.get('promotion_description'):
                    print(f"     Promo: {p['promotion_description']}")
    
    print("\n" + "="*70)
    print("TEST COMPLETADO ✅")
    print("="*70)

if __name__ == "__main__":
    try:
        test_promotions()
    except Exception as e:
        print(f"\n❌ Error durante el test: {str(e)}")
        import traceback
        traceback.print_exc()
