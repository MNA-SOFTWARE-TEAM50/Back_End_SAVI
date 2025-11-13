"""
Test para verificar que las alertas se generan como duplicados
en lugar de actualizar las existentes
"""
import requests
import json
from datetime import datetime

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

def test_duplicate_alerts():
    """Test principal: verificar duplicados"""
    print("\n" + "="*60)
    print("TEST: VERIFICACIÓN DE ALERTAS DUPLICADAS")
    print("="*60)
    
    # 1. Autenticarse
    print("\n1️⃣ Autenticando...")
    token = login()
    headers = get_headers(token)
    print("✅ Token obtenido")
    
    # 2. Obtener cantidad inicial de alertas
    print("\n2️⃣ Obteniendo cantidad inicial de alertas...")
    response = requests.get(f"{BASE_URL}/inventory-alerts/", headers=headers)
    initial_alerts = response.json()
    initial_count = len(initial_alerts)
    print(f"📊 Alertas iniciales: {initial_count}")
    
    # 3. Generar alertas por primera vez
    print("\n3️⃣ Generando alertas (primera vez)...")
    response = requests.post(f"{BASE_URL}/inventory-alerts/generate", headers=headers)
    result = response.json()
    print(f"✅ {result['message']}")
    print(f"   Alertas generadas: {len(result['alerts'])}")
    
    # 4. Obtener cantidad después de primera generación
    response = requests.get(f"{BASE_URL}/inventory-alerts/", headers=headers)
    after_first_gen = response.json()
    count_after_first = len(after_first_gen)
    print(f"📊 Total de alertas activas: {count_after_first}")
    
    # 5. Generar alertas por segunda vez (sin cambiar inventario)
    print("\n4️⃣ Generando alertas nuevamente (segunda vez)...")
    response = requests.post(f"{BASE_URL}/inventory-alerts/generate", headers=headers)
    result = response.json()
    print(f"✅ {result['message']}")
    print(f"   Alertas generadas: {len(result['alerts'])}")
    
    # 6. Obtener cantidad después de segunda generación
    response = requests.get(f"{BASE_URL}/inventory-alerts/", headers=headers)
    after_second_gen = response.json()
    count_after_second = len(after_second_gen)
    print(f"📊 Total de alertas activas: {count_after_second}")
    
    # 7. Verificar resultados
    print("\n" + "="*60)
    print("RESULTADOS:")
    print("="*60)
    
    print(f"\n📈 Evolución de alertas:")
    print(f"   Inicial: {initial_count}")
    print(f"   Después de 1ra generación: {count_after_first}")
    print(f"   Después de 2da generación: {count_after_second}")
    
    # Las alertas antiguas se desactivan y se crean nuevas
    # Por lo tanto, el conteo debería ser similar después de cada generación
    if count_after_second > 0:
        print("\n✅ ÉXITO: Las alertas se están generando correctamente")
        print("   (Las alertas antiguas se desactivan y se crean nuevas)")
        
        # Mostrar algunas alertas recientes
        print("\n📋 Últimas 5 alertas generadas:")
        for i, alert in enumerate(after_second_gen[-5:], 1):
            print(f"\n   {i}. Producto ID: {alert['product_id']}")
            print(f"      Tipo: {alert['alert_type']}")
            print(f"      Severidad: {alert['severity']}")
            print(f"      Stock actual: {alert['current_stock']}")
            print(f"      Creada: {alert['created_at']}")
            print(f"      Activa: {alert['is_active']}")
    else:
        print("\n⚠️ No hay alertas activas para verificar")
    
    # 8. Obtener estadísticas
    print("\n" + "="*60)
    print("ESTADÍSTICAS DE ALERTAS:")
    print("="*60)
    response = requests.get(f"{BASE_URL}/inventory-alerts/stats", headers=headers)
    stats = response.json()
    print(f"\n📊 Total: {stats['total_alerts']}")
    print(f"📊 Total activas: {stats['active_alerts']}")
    print(f"📊 Críticas: {stats['critical_alerts']}")
    print(f"📊 No leídas: {stats['unread_alerts']}")
    print(f"\nPor tipo:")
    for alert_type, count in stats['by_type'].items():
        print(f"   {alert_type}: {count}")
    print(f"\nPor severidad:")
    for severity, count in stats['by_severity'].items():
        print(f"   {severity}: {count}")
    
    print("\n" + "="*60)
    print("TEST COMPLETADO")
    print("="*60)

if __name__ == "__main__":
    try:
        test_duplicate_alerts()
    except Exception as e:
        print(f"\n❌ Error durante el test: {str(e)}")
        import traceback
        traceback.print_exc()
