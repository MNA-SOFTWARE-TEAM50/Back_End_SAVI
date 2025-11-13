"""
Script de ejemplo para integración del sistema de alertas
Este script puede ejecutarse como tarea programada
"""
import requests
import os
from datetime import datetime
import logging

# Configuración
BASE_URL = os.getenv("SAVI_API_URL", "http://localhost:8000/api/v1")
ADMIN_TOKEN = os.getenv("SAVI_ADMIN_TOKEN", None)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_auth_token(username="admin", password="admin123"):
    """Obtener token de autenticación"""
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data={"username": username, "password": password}
        )
        response.raise_for_status()
        token = response.json()["access_token"]
        logger.info(f"✓ Autenticación exitosa como '{username}'")
        return token
    except Exception as e:
        logger.error(f"✗ Error en autenticación: {e}")
        return None


def generate_alerts(token, config=None):
    """Generar alertas de inventario"""
    if config is None:
        config = {
            "low_stock_threshold": 10,
            "critical_stock_threshold": 5,
            "no_movement_days": 30,
            "auto_generate_alerts": True
        }
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(
            f"{BASE_URL}/inventory-alerts/generate",
            headers=headers,
            json=config
        )
        response.raise_for_status()
        data = response.json()
        
        logger.info(f"✓ {data['message']}")
        if data.get('alerts'):
            logger.info(f"  Alertas generadas:")
            for alert in data['alerts'][:10]:  # Mostrar primeras 10
                logger.info(f"    • {alert}")
        
        return data
    except Exception as e:
        logger.error(f"✗ Error generando alertas: {e}")
        return None


def get_critical_alerts(token):
    """Obtener alertas críticas"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}/inventory-alerts/",
            headers=headers,
            params={"severity": "critical", "active_only": True}
        )
        response.raise_for_status()
        alerts = response.json()
        
        if alerts:
            logger.warning(f"⚠️  {len(alerts)} alertas críticas encontradas:")
            for alert in alerts:
                logger.warning(f"  • {alert['product_name']}: {alert['message']}")
        else:
            logger.info("✓ No hay alertas críticas")
        
        return alerts
    except Exception as e:
        logger.error(f"✗ Error obteniendo alertas críticas: {e}")
        return []


def get_stats(token):
    """Obtener estadísticas de alertas"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}/inventory-alerts/stats",
            headers=headers
        )
        response.raise_for_status()
        stats = response.json()
        
        logger.info("📊 Estadísticas de Alertas:")
        logger.info(f"  Total: {stats['total_alerts']}")
        logger.info(f"  Activas: {stats['active_alerts']}")
        logger.info(f"  No leídas: {stats['unread_alerts']}")
        logger.info(f"  Críticas: {stats['critical_alerts']}")
        
        return stats
    except Exception as e:
        logger.error(f"✗ Error obteniendo estadísticas: {e}")
        return None


def send_email_notification(alerts):
    """
    Enviar notificación por email (ejemplo)
    Requiere configurar SMTP
    """
    if not alerts:
        return
    
    # Aquí iría la lógica de envío de email
    # Por ahora solo log
    logger.info(f"📧 Se enviaría email con {len(alerts)} alertas críticas")
    
    # Ejemplo con smtplib:
    # import smtplib
    # from email.mime.text import MIMEText
    # 
    # msg = MIMEText(f"Hay {len(alerts)} alertas críticas...")
    # msg['Subject'] = 'SAVI - Alertas Críticas de Inventario'
    # msg['From'] = 'savi@example.com'
    # msg['To'] = 'admin@example.com'
    # 
    # with smtplib.SMTP('localhost') as s:
    #     s.send_message(msg)


def main():
    """Función principal"""
    logger.info("="*60)
    logger.info("SAVI - Generación Automática de Alertas")
    logger.info(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*60)
    
    # 1. Autenticación
    token = ADMIN_TOKEN or get_auth_token()
    if not token:
        logger.error("No se pudo obtener token de autenticación")
        return 1
    
    # 2. Generar alertas
    logger.info("\n--- Generando Alertas ---")
    result = generate_alerts(token)
    
    if not result:
        return 1
    
    # 3. Obtener estadísticas
    logger.info("\n--- Estadísticas ---")
    stats = get_stats(token)
    
    # 4. Verificar alertas críticas
    logger.info("\n--- Alertas Críticas ---")
    critical = get_critical_alerts(token)
    
    # 5. Notificaciones (si hay críticas)
    if critical:
        send_email_notification(critical)
    
    logger.info("\n" + "="*60)
    logger.info("✓ Proceso completado exitosamente")
    logger.info("="*60)
    
    return 0


if __name__ == "__main__":
    exit(main())
