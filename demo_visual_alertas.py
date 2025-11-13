"""
Script de demostración visual del sistema de alertas
Genera datos de prueba y muestra cómo se ven en la interfaz
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"
USERNAME = "admin"
PASSWORD = "admin123"

print("=" * 70)
print("  🎨 DEMOSTRACIÓN VISUAL DEL SISTEMA DE ALERTAS DE INVENTARIO")
print("=" * 70)
print()

# 1. Login
print("1️⃣  Autenticando...")
response = requests.post(
    f"{BASE_URL}/auth/login",
    data={"username": USERNAME, "password": PASSWORD}
)

if response.status_code != 200:
    print("❌ Error al autenticar. Verifica que el servidor esté corriendo.")
    exit(1)

token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("✅ Autenticado como admin\n")

# 2. Generar alertas
print("2️⃣  Generando alertas automáticas...")
print("   Configuración:")
print("   • Stock bajo: ≤ 10 unidades")
print("   • Stock crítico: ≤ 5 unidades")
print("   • Sin movimiento: 30 días\n")

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

# 3. Obtener estadísticas
print("3️⃣  Estadísticas de alertas:")
response = requests.get(f"{BASE_URL}/inventory-alerts/stats", headers=headers)

if response.status_code == 200:
    stats = response.json()
    
    print("┌─────────────────────────────────────────────────────────┐")
    print(f"│  📊 Total de alertas:      {str(stats['total_alerts']).rjust(3)} alertas         │")
    print(f"│  🔵 Alertas activas:       {str(stats['active_alerts']).rjust(3)} alertas         │")
    print(f"│  📬 Alertas no leídas:     {str(stats['unread_alerts']).rjust(3)} alertas         │")
    print(f"│  🔴 Alertas críticas:      {str(stats['critical_alerts']).rjust(3)} alertas         │")
    print("└─────────────────────────────────────────────────────────┘")
    print()

# 4. Mostrar alertas por severidad
print("4️⃣  Alertas por severidad:")
response = requests.get(
    f"{BASE_URL}/inventory-alerts/",
    headers=headers,
    params={"active_only": True, "limit": 100}
)

if response.status_code == 200:
    alerts = response.json()
    
    # Agrupar por severidad
    by_severity = {
        'critical': [],
        'high': [],
        'medium': [],
        'low': []
    }
    
    for alert in alerts:
        by_severity[alert['severity']].append(alert)
    
    # Mostrar cada grupo
    severity_info = {
        'critical': ('🔴 CRÍTICAS', 'Requieren acción inmediata'),
        'high': ('🟠 ALTAS', 'Atención prioritaria'),
        'medium': ('🟡 MEDIAS', 'Revisar pronto'),
        'low': ('🟢 BAJAS', 'Informativas')
    }
    
    for severity in ['critical', 'high', 'medium', 'low']:
        alerts_list = by_severity[severity]
        if alerts_list:
            icon, desc = severity_info[severity]
            print(f"\n{icon} - {desc}")
            print("─" * 70)
            for alert in alerts_list[:5]:  # Mostrar max 5 por grupo
                print(f"  • {alert['product_name']}")
                print(f"    {alert['message']}")
                if alert['current_stock'] is not None:
                    print(f"    Stock actual: {alert['current_stock']} unidades")
                print()
            
            if len(alerts_list) > 5:
                print(f"  ... y {len(alerts_list) - 5} alertas más\n")

# 5. Vista previa de cómo se ve en la interfaz
print("\n5️⃣  Vista previa de la interfaz web:")
print("=" * 70)
print()
print("┌────────────────────────────────────────────────────────────────┐")
print("│  🏠 SAVI > Inventario                                          │")
print("├────────────────────────────────────────────────────────────────┤")
print("│                                                                 │")
print("│  Inventario          [🔔 Generar Alertas] [+ Agregar Producto]│")
print("│                                                                 │")
print("├────────────────────────────────────────────────────────────────┤")

if stats and stats['active_alerts'] > 0:
    print("│  ⚠️  ALERTAS DE INVENTARIO                [Ver Detalles →]  │")
    print("│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │")
    print(f"│  │   {str(stats['active_alerts']).rjust(2)}     │  │   {str(stats['critical_alerts']).rjust(2)}     │  │   {str(stats['unread_alerts']).rjust(2)}     │  │   {str(stats['total_alerts']).rjust(2)}     │   │")
    print("│  │ Activas  │  │ Críticas │  │ Sin Leer │  │  Total   │   │")
    print("│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │")
    print("│                                                             │")
else:
    print("│  ✅ No hay alertas activas                                  │")
    print("│                                                             │")

print("├────────────────────────────────────────────────────────────────┤")
print("│  🔍 Buscar...          [Categorías ▼]                         │")
print("├────────────────────────────────────────────────────────────────┤")
print("│                                                                 │")
print("│  Imagen │ SKU  │ Producto      │ Cat. │ Precio │ Stock        │")
print("│─────────┼──────┼───────────────┼──────┼────────┼──────────────│")

# Mostrar algunos productos de ejemplo
if response.status_code == 200 and alerts:
    for i, alert in enumerate(alerts[:5]):
        severity_icons = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🟢'
        }
        icon = severity_icons.get(alert['severity'], '⚪')
        
        # Simular visualización
        product_name = alert['product_name'][:12].ljust(12)
        stock = str(alert.get('current_stock', 0)).rjust(3)
        warning = '⚠️ ' if alert['current_stock'] and alert['current_stock'] <= 10 else '  '
        
        print(f"│{icon} [📷]! │ ... │ {product_name} │ ... │ $... │ {stock} {warning}│")
        
        if i == 0:  # Solo mostrar detalles del primero
            alert_type_text = {
                'low_stock': 'Stock bajo',
                'no_stock': 'Sin stock',
                'no_movement': 'Sin movimiento'
            }
            print(f"│         │      │ [{icon}] ⚠️  {alert_type_text.get(alert['alert_type'], '')}     │")

print("│  ...    │ ...  │ ...           │ ... │ ...    │ ...          │")
print("└────────────────────────────────────────────────────────────────┘")

print()
print("=" * 70)
print()

# 6. Instrucciones para ver en el navegador
print("6️⃣  Para ver en el navegador:")
print()
print("   1. Asegúrate de que el frontend esté corriendo:")
print("      cd Front_End_SAVI && npm run dev")
print()
print("   2. Abre tu navegador en:")
print("      http://localhost:5173/inventory")
print()
print("   3. Verás:")
print("      • Panel naranja con estadísticas de alertas")
print("      • Botón 'Generar Alertas' en la parte superior")
print("      • Productos con alertas resaltados con bordes de colores")
print("      • Iconos de alerta (!) en las imágenes de productos")
print("      • Stock en colores según nivel (rojo/naranja/amarillo)")
print()
print("   4. Haz clic en 'Ver Detalles' para expandir el panel de alertas")
print()

print("=" * 70)
print("✅ Demostración completada")
print("=" * 70)
