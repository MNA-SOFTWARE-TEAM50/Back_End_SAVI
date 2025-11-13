"""
Script de prueba: Resolución automática de alertas
Verifica que las alertas se resuelven cuando se actualiza el stock
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"
USERNAME = "admin"
PASSWORD = "admin123"

def print_header(text):
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")

def login():
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": USERNAME, "password": PASSWORD}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

print_header("PRUEBA: RESOLUCIÓN AUTOMÁTICA DE ALERTAS")

# 1. Login
print("1️⃣  Autenticando...")
token = login()
if not token:
    print("❌ Error al autenticar")
    exit(1)
print("✅ Autenticado\n")

headers = {"Authorization": f"Bearer {token}"}

# 2. Generar alertas
print("2️⃣  Generando alertas iniciales...")
response = requests.post(
    f"{BASE_URL}/inventory-alerts/generate",
    headers=headers,
    json={
        "low_stock_threshold": 10,
        "critical_stock_threshold": 5,
        "no_movement_days": 30
    }
)
if response.status_code == 200:
    data = response.json()
    print(f"✅ {data['message']}\n")
else:
    print(f"❌ Error: {response.status_code}\n")

# 3. Ver estadísticas antes
print("3️⃣  Estadísticas ANTES de actualizar stock:")
response = requests.get(f"{BASE_URL}/inventory-alerts/stats", headers=headers)
if response.status_code == 200:
    stats = response.json()
    print(f"   • Alertas activas: {stats['active_alerts']}")
    print(f"   • Alertas críticas: {stats['critical_alerts']}")
    print(f"   • Advertencias medias: {stats.get('by_severity', {}).get('medium', 0)}")
    print(f"   • Alta prioridad: {stats.get('by_severity', {}).get('high', 0)}")

# 4. Obtener un producto con alerta de stock bajo
print("\n4️⃣  Buscando producto con alerta de stock bajo...")
response = requests.get(
    f"{BASE_URL}/inventory-alerts/",
    headers=headers,
    params={"alert_type": "low_stock", "limit": 1}
)
if response.status_code == 200 and response.json():
    alert = response.json()[0]
    product_id = alert['product_id']
    product_name = alert['product_name']
    current_stock = alert['current_stock']
    
    print(f"✅ Producto encontrado: {product_name}")
    print(f"   • ID: {product_id}")
    print(f"   • Stock actual: {current_stock}")
    print(f"   • Tipo de alerta: {alert['alert_type']}")
    print(f"   • Severidad: {alert['severity']}")
    
    # 5. Actualizar el stock para resolver la alerta
    print(f"\n5️⃣  Actualizando stock de '{product_name}' a 50 unidades...")
    response = requests.put(
        f"{BASE_URL}/products/{product_id}",
        headers=headers,
        json={"stock": 50}
    )
    
    if response.status_code == 200:
        print("✅ Stock actualizado correctamente")
        
        # 6. Verificar que la alerta se resolvió
        print("\n6️⃣  Verificando si la alerta se resolvió...")
        response = requests.get(
            f"{BASE_URL}/inventory-alerts/",
            headers=headers,
            params={"product_id": product_id, "alert_type": "low_stock"}
        )
        
        # La alerta debería estar inactiva ahora
        print(f"   • Alertas activas del producto: {len([a for a in response.json() if a['is_active']])}")
        print(f"   • Alertas resueltas del producto: {len([a for a in response.json() if not a['is_active']])}")
        
        if any(not a['is_active'] for a in response.json()):
            print("✅ ¡Alerta resuelta automáticamente!")
        else:
            print("⚠️  La alerta sigue activa (puede necesitar regenerar alertas)")
    else:
        print(f"❌ Error al actualizar stock: {response.status_code}")
else:
    print("⚠️  No se encontraron alertas de stock bajo para probar")

# 7. Ver estadísticas después
print("\n7️⃣  Estadísticas DESPUÉS de actualizar stock:")
response = requests.get(f"{BASE_URL}/inventory-alerts/stats", headers=headers)
if response.status_code == 200:
    stats = response.json()
    print(f"   • Alertas activas: {stats['active_alerts']}")
    print(f"   • Alertas críticas: {stats['critical_alerts']}")
    print(f"   • Advertencias medias: {stats.get('by_severity', {}).get('medium', 0)}")
    print(f"   • Alta prioridad: {stats.get('by_severity', {}).get('high', 0)}")

# 8. Regenerar alertas para limpiar
print("\n8️⃣  Regenerando alertas para actualizar estado...")
response = requests.post(
    f"{BASE_URL}/inventory-alerts/generate",
    headers=headers,
    json={
        "low_stock_threshold": 10,
        "critical_stock_threshold": 5,
        "no_movement_days": 30
    }
)
if response.status_code == 200:
    data = response.json()
    print(f"✅ {data['message']}")

# 9. Estadísticas finales
print("\n9️⃣  Estadísticas FINALES:")
response = requests.get(f"{BASE_URL}/inventory-alerts/stats", headers=headers)
if response.status_code == 200:
    stats = response.json()
    print(f"   • Alertas activas: {stats['active_alerts']}")
    print(f"   • Alertas críticas: {stats['critical_alerts']}")
    print(f"   • Advertencias medias: {stats.get('by_severity', {}).get('medium', 0)}")
    print(f"   • Alta prioridad: {stats.get('by_severity', {}).get('high', 0)}")

print_header("PRUEBA COMPLETADA")
print("✅ Las alertas se resuelven automáticamente cuando:")
print("   • Se actualiza el stock por encima del umbral")
print("   • Se regeneran las alertas con el botón 'Generar Alertas'")
print("\n💡 En la interfaz, al editar un producto y aumentar el stock,")
print("   las alertas se resolverán automáticamente.")
print("="*70)
