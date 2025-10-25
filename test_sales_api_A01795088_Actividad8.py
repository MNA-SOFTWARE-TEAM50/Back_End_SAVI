"""
Script para probar operaciones CRUD del API de Ventas (Sales)
Autor: Equipo 50 SAVI
Fecha: 2025-10-21
"""

import requests
import json

# URL base del API
BASE_URL = "http://localhost:8000/api"

# Credenciales
USERNAME = "admin"
PASSWORD = "admin123"

# Variable global para almacenar el token
TOKEN = None

# ----------------------------------------------------
# A. Autenticación - Obtener token JWT
# ----------------------------------------------------
def login():
    global TOKEN
    url = f"{BASE_URL}/v1/auth/login"
    print(f"\nIntentando autenticarse como '{USERNAME}'...")
    
    try:
        # OAuth2PasswordRequestForm requiere enviar como form data, no JSON
        data = {
            "username": USERNAME,
            "password": PASSWORD
        }
        # Usar 'data' en lugar de 'json' para enviar como form-urlencoded
        response = requests.post(url, data=data)
        
        if response.status_code == 200:
            result = response.json()    
            TOKEN = result.get("access_token")
            print("✅ Autenticación exitosa")
            print(f"Token obtenido: {TOKEN[:30]}...")
            return True
        else:
            print(f"❌ Error de autenticación. Código: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Error de conexión. Asegúrate de que el backend esté corriendo en http://localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

# ----------------------------------------------------
# B. GET - Obtener todas las ventas
# ----------------------------------------------------
def get_all_sales():
    print("\n" + "="*60)
    print("GET - Obteniendo lista de ventas...")
    print("="*60)
    
    try:
        url = f"{BASE_URL}/v1/sales?limit=5"
        headers = {"Authorization": f"Bearer {TOKEN}"}
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Ventas obtenidas exitosamente")
            print(f"Total de registros: {data.get('total', 0)}")
            print(f"\nPrimeras {len(data.get('items', []))} ventas:")
            print(json.dumps(data, indent=4))
        else:
            print(f"\n❌ Error al obtener ventas. Código: {response.status_code}")
            print(f"Respuesta: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Error de conexión")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

# ----------------------------------------------------
# C. GET - Obtener una venta por ID
# ----------------------------------------------------
def get_sale_by_id(sale_id):
    print("\n" + "="*60)
    print(f"GET - Obteniendo venta con ID: {sale_id}...")
    print("="*60)
    
    try:
        url = f"{BASE_URL}/v1/sales/{sale_id}"
        headers = {"Authorization": f"Bearer {TOKEN}"}
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Venta encontrada:")
            print(json.dumps(data, indent=4))
        elif response.status_code == 404:
            print(f"\n⚠️ Venta con ID {sale_id} no encontrada")
        else:
            print(f"\n❌ Error al obtener venta. Código: {response.status_code}")
            print(f"Respuesta: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Error de conexión")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

# ----------------------------------------------------
# D. POST - Crear una nueva venta
# ----------------------------------------------------
def create_sale():
    print("\n" + "="*60)
    print("POST - Creando nueva venta...")
    print("="*60)
    
    try:
        url = f"{BASE_URL}/v1/sales/"
        headers = {"Authorization": f"Bearer {TOKEN}"}
        
        # Datos de la venta de prueba
        sale_data = {
            "items": [
                {
                    "product_id": 1,
                    "product_name": "Producto Prueba 1",
                    "quantity": 2,
                    "unit_price": 100.00,
                    "subtotal": 200.00
                },
                {
                    "product_id": 2,
                    "product_name": "Producto Prueba 2",
                    "quantity": 1,
                    "unit_price": 50.00,
                    "subtotal": 50.00
                }
            ],
            "subtotal": 250.00,
            "tax": 40.00,
            "discount": 0.00,
            "total": 290.00,
            "payment_method": "cash"
        }
        
        print("\nDatos de la venta:")
        print(json.dumps(sale_data, indent=4))
        
        response = requests.post(url, json=sale_data, headers=headers)
        
        if response.status_code in [200, 201]:
            result = response.json()
            sale_id = result.get('id')
            print(f"\n✅ Venta creada exitosamente")
            print(f"ID de la nueva venta: {sale_id}")
            print(json.dumps(result, indent=4))
            return sale_id
        else:
            print(f"\n❌ Error al crear venta. Código: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Error de conexión")
        return None
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return None

# ----------------------------------------------------
# E. PUT - Actualizar una venta
# ----------------------------------------------------
def update_sale(sale_id):
    print("\n" + "="*60)
    print(f"PUT - Actualizando venta con ID: {sale_id}...")
    print("="*60)
    
    try:
        url = f"{BASE_URL}/v1/sales/{sale_id}"
        headers = {"Authorization": f"Bearer {TOKEN}"}
        
        # Datos a actualizar
        update_data = {
            "status": "completed"
        }
        
        print("\nDatos a actualizar:")
        print(json.dumps(update_data, indent=4))
        
        response = requests.put(url, json=update_data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Venta actualizada exitosamente")
            print(json.dumps(result, indent=4))
            return True
        else:
            print(f"\n❌ Error al actualizar venta. Código: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Error de conexión")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

# ----------------------------------------------------
# F. DELETE - Eliminar una venta
# ----------------------------------------------------
def delete_sale(sale_id):
    print("\n" + "="*60)
    print(f"DELETE - Eliminando venta con ID: {sale_id}...")
    print("="*60)
    
    try:
        url = f"{BASE_URL}/v1/sales/{sale_id}"
        headers = {"Authorization": f"Bearer {TOKEN}"}
        
        response = requests.delete(url, headers=headers)
        
        if response.status_code in [200, 204]:
            print(f"\n✅ Venta eliminada exitosamente")
            return True
        else:
            print(f"\n❌ Error al eliminar venta. Código: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Error de conexión")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False


# ----------------------------------------------------
# MAIN - Ejecutar todas las operaciones
# ----------------------------------------------------
if __name__ == '__main__':
    print("\n" + "#"*60)
    print("#  SCRIPT DE PRUEBA - API DE VENTAS (CRUD)".center(60))
    print("#"*60)
    
    # 1. Autenticarse
    if not login():
        print("\n❌ No se pudo autenticar. Terminando script.")
        exit(1)
    
    # 2. Obtener todas las ventas
    get_all_sales()
    
    # 3. Obtener una venta específica (ID 1)
    get_sale_by_id(sale_id=1)
    
    # 4. Crear una nueva venta
    new_sale_id = create_sale()
    
    if new_sale_id:
        # 5. Obtener la venta recién creada
        get_sale_by_id(sale_id=new_sale_id)
        
        # 6. Actualizar la venta
        update_sale(sale_id=new_sale_id)
        
        # 7. Verificar la actualización
        get_sale_by_id(sale_id=new_sale_id)
        
        # 8. Eliminar la venta
        delete_sale(sale_id=new_sale_id)
        
        # 9. Verificar que fue eliminada (debería dar 404)
        get_sale_by_id(sale_id=new_sale_id)
    
    print("\n" + "#"*60)
    print("#  PRUEBAS COMPLETADAS".center(60))
    print("#"*60 + "\n")
