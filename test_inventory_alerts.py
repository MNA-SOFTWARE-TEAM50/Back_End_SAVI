"""
Script de prueba para el sistema de Alertas de Inventario
"""
import requests
import json
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:8000/api/v1"
USERNAME = "admin"
PASSWORD = "admin123"

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}")
    print(f"{text}")
    print(f"{'='*60}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")

def login():
    """Obtener token de acceso"""
    print_header("1. Autenticación")
    
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": USERNAME, "password": PASSWORD}
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print_success(f"Login exitoso como '{USERNAME}'")
        return token
    else:
        print_error(f"Error en login: {response.status_code}")
        print(response.text)
        return None

def test_generate_alerts(token):
    """Generar alertas automáticas"""
    print_header("2. Generar Alertas Automáticas")
    
    headers = {"Authorization": f"Bearer {token}"}
    config = {
        "low_stock_threshold": 10,
        "critical_stock_threshold": 5,
        "no_movement_days": 30,
        "auto_generate_alerts": True
    }
    
    response = requests.post(
        f"{BASE_URL}/inventory-alerts/generate",
        headers=headers,
        json=config
    )
    
    if response.status_code == 200:
        data = response.json()
        print_success(f"Alertas generadas: {data['message']}")
        if data['alerts']:
            print_info("Alertas creadas:")
            for alert in data['alerts'][:5]:  # Mostrar solo las primeras 5
                print(f"  • {alert}")
            if len(data['alerts']) > 5:
                print(f"  ... y {len(data['alerts']) - 5} más")
        return True
    else:
        print_error(f"Error generando alertas: {response.status_code}")
        print(response.text)
        return False

def test_get_stats(token):
    """Obtener estadísticas de alertas"""
    print_header("3. Estadísticas de Alertas")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/inventory-alerts/stats", headers=headers)
    
    if response.status_code == 200:
        stats = response.json()
        print_success("Estadísticas obtenidas:")
        print(f"\n  Total de alertas: {stats['total_alerts']}")
        print(f"  Alertas activas: {stats['active_alerts']}")
        print(f"  Alertas no leídas: {stats['unread_alerts']}")
        print(f"  Alertas críticas: {stats['critical_alerts']}")
        
        if stats['by_type']:
            print("\n  Por tipo:")
            for alert_type, count in stats['by_type'].items():
                print(f"    - {alert_type}: {count}")
        
        if stats['by_severity']:
            print("\n  Por severidad:")
            for severity, count in stats['by_severity'].items():
                print(f"    - {severity}: {count}")
        
        return True
    else:
        print_error(f"Error obteniendo estadísticas: {response.status_code}")
        return False

def test_list_alerts(token):
    """Listar alertas"""
    print_header("4. Listar Alertas")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Alertas activas
    print_info("Alertas activas:")
    response = requests.get(
        f"{BASE_URL}/inventory-alerts/",
        headers=headers,
        params={"active_only": True, "limit": 5}
    )
    
    if response.status_code == 200:
        alerts = response.json()
        if alerts:
            for alert in alerts:
                severity_icon = {
                    "critical": "🔴",
                    "high": "🟠",
                    "medium": "🟡",
                    "low": "🟢"
                }.get(alert['severity'], "⚪")
                
                print(f"\n  {severity_icon} [{alert['severity'].upper()}] {alert['product_name']}")
                print(f"     Tipo: {alert['alert_type']}")
                print(f"     Mensaje: {alert['message']}")
                print(f"     Stock actual: {alert['current_stock']}")
                print(f"     Leída: {'Sí' if alert['is_read'] else 'No'}")
        else:
            print_info("  No hay alertas activas")
        return True
    else:
        print_error(f"Error listando alertas: {response.status_code}")
        return False

def test_alert_actions(token):
    """Probar acciones sobre alertas"""
    print_header("5. Acciones sobre Alertas")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Obtener primera alerta
    response = requests.get(
        f"{BASE_URL}/inventory-alerts/",
        headers=headers,
        params={"limit": 1, "unread_only": True}
    )
    
    if response.status_code == 200:
        alerts = response.json()
        if alerts:
            alert_id = alerts[0]['id']
            
            # Marcar como leída
            print_info(f"Marcando alerta {alert_id} como leída...")
            response = requests.post(
                f"{BASE_URL}/inventory-alerts/{alert_id}/mark-read",
                headers=headers
            )
            if response.status_code == 200:
                print_success("Alerta marcada como leída")
            
            # Obtener detalles
            print_info(f"Obteniendo detalles de alerta {alert_id}...")
            response = requests.get(
                f"{BASE_URL}/inventory-alerts/{alert_id}",
                headers=headers
            )
            if response.status_code == 200:
                alert = response.json()
                print_success(f"Detalles obtenidos: {alert['product_name']}")
            
            return True
        else:
            print_info("No hay alertas sin leer para probar")
            return True
    else:
        print_error(f"Error: {response.status_code}")
        return False

def test_filter_alerts(token):
    """Probar filtros de alertas"""
    print_header("6. Filtrar Alertas")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Por severidad crítica
    print_info("Alertas críticas:")
    response = requests.get(
        f"{BASE_URL}/inventory-alerts/",
        headers=headers,
        params={"severity": "critical", "limit": 3}
    )
    
    if response.status_code == 200:
        alerts = response.json()
        print_success(f"Encontradas {len(alerts)} alertas críticas")
        for alert in alerts:
            print(f"  • {alert['product_name']}: {alert['message'][:50]}...")
    
    # Por tipo low_stock
    print_info("\nAlertas de stock bajo:")
    response = requests.get(
        f"{BASE_URL}/inventory-alerts/",
        headers=headers,
        params={"alert_type": "low_stock", "limit": 3}
    )
    
    if response.status_code == 200:
        alerts = response.json()
        print_success(f"Encontradas {len(alerts)} alertas de stock bajo")
        for alert in alerts:
            print(f"  • {alert['product_name']}: Stock actual {alert['current_stock']}")
    
    return True

def main():
    print(f"{Colors.BOLD}{Colors.HEADER}")
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║     PRUEBAS DEL SISTEMA DE ALERTAS DE INVENTARIO         ║")
    print("║                      SAVI v1.0                            ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}")
    
    print_info(f"Servidor: {BASE_URL}")
    print_info(f"Usuario: {USERNAME}")
    print_info(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Login
    token = login()
    if not token:
        print_error("No se pudo autenticar. Verifica que el servidor esté corriendo.")
        return
    
    # Ejecutar pruebas
    tests = [
        ("Generar alertas", lambda: test_generate_alerts(token)),
        ("Estadísticas", lambda: test_get_stats(token)),
        ("Listar alertas", lambda: test_list_alerts(token)),
        ("Acciones sobre alertas", lambda: test_alert_actions(token)),
        ("Filtrar alertas", lambda: test_filter_alerts(token))
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print_error(f"Error en prueba '{name}': {str(e)}")
            failed += 1
    
    # Resumen
    print_header("Resumen de Pruebas")
    print(f"✓ Pruebas exitosas: {Colors.OKGREEN}{passed}{Colors.ENDC}")
    print(f"✗ Pruebas fallidas: {Colors.FAIL}{failed}{Colors.ENDC}")
    print(f"Total: {passed + failed}")
    
    if failed == 0:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}¡Todas las pruebas pasaron exitosamente!{Colors.ENDC}")
    else:
        print(f"\n{Colors.WARNING}Algunas pruebas fallaron. Revisa los detalles arriba.{Colors.ENDC}")

if __name__ == "__main__":
    main()
