# Guía de Instalación - Backend SAVI

## 🤖 Instalación Automatizada (Recomendado)

Ejecuta el script de instalación automatizada:

```powershell
.\install.ps1
```

Este script hace todo automáticamente:
- ✅ Verifica Python
- ✅ Crea entorno virtual
- ✅ Instala todas las dependencias (incluyendo versiones específicas)
- ✅ Configura el archivo .env
- ✅ Te guía en los próximos pasos

**Después del script, solo necesitas:**
1. Crear la base de datos MySQL
2. Ejecutar `python init_db.py`
3. Ejecutar `uvicorn main:app --reload`

---

## ⚡ Instalación Manual (Copiar y Pegar)

```powershell
# 1. Navegar al directorio del backend
cd C:\Users\LmCas\OneDrive\Documentos\Desarrollo\Maestria\SAVI\Back_End_SAVI

# 2. Crear y activar entorno virtual
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Actualizar pip
python -m pip install --upgrade pip

# 4. Instalar todas las dependencias
pip install -r requirements.txt
pip install bcrypt==4.0.1 passlib==1.7.4
pip install python-jose[cryptography]

# 5. Crear base de datos MySQL (ejecutar en MySQL)
# CREATE DATABASE savidb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 6. Inicializar base de datos
python init_db.py

# 7. Iniciar servidor
uvicorn main:app --reload
```

**¡Listo!** El servidor estará en http://localhost:8000

---

## 📋 Requisitos Previos

- Python 3.11 o superior
- MySQL Server 8.0 o superior
- pip (gestor de paquetes de Python)

## 🔧 Instalación

### 1. Verificar Python

```powershell
python --version
```

Debe mostrar Python 3.11 o superior.

### 2. Crear entorno virtual

```powershell
cd Back_End_SAVI
python -m venv venv
```

### 3. Activar entorno virtual

**PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1
```

Si obtienes un error de permisos, ejecuta:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**CMD:**
```powershell
.\venv\Scripts\activate.bat
```

### 4. Actualizar pip

```powershell
python -m pip install --upgrade pip
```

### 5. Instalar dependencias

```powershell
pip install -r requirements.txt
```

Esto instalará:
- FastAPI - Framework web
- Uvicorn - Servidor ASGI
- SQLAlchemy - ORM
- aiomysql - Driver MySQL asíncrono
- Pydantic - Validación de datos
- python-jose - JWT para autenticación
- passlib - Hashing de contraseñas
- Y más...

### 6. Instalar dependencias adicionales

**IMPORTANTE:** Instala estas versiones específicas para evitar conflictos:

```powershell
pip install bcrypt==4.0.1 passlib==1.7.4
```

```powershell
pip install python-jose[cryptography]
```

Estas dependencias son necesarias para:
- `bcrypt==4.0.1` - Versión compatible con passlib para hashing de contraseñas
- `passlib==1.7.4` - Librería de hashing de contraseñas
- `python-jose` - Manejo de tokens JWT para autenticación

## 🗄️ Configurar Base de Datos MySQL

### 1. Crear la base de datos

Conectarse a MySQL y ejecutar:

```sql
CREATE DATABASE savidb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. Verificar conexión

La cadena de conexión ya está configurada en `.env`:
```
DATABASE_URL=mysql+aiomysql://root:Mc4stroG+@localhost:3306/savidb
```

Si necesitas cambiar las credenciales, edita el archivo `.env`.

**NOTA IMPORTANTE:** La estructura del proyecto ha sido simplificada. Todo el código que antes estaba en `app/` ahora está directamente en la raíz de `Back_End_SAVI/`. Esto facilita las importaciones y el mantenimiento del código.

### 3. Inicializar tablas y datos de prueba

```powershell
python init_db.py
```

Este script:
- ✅ Crea todas las tablas en MySQL
- ✅ Inserta usuarios de prueba (admin y cajero)
- ✅ Inserta 5 productos de ejemplo
- ✅ Inserta 3 clientes de ejemplo

## 🚀 Iniciar el Servidor

### Modo desarrollo (con auto-reload)

**IMPORTANTE:** Asegúrate de estar en el directorio `Back_End_SAVI` antes de ejecutar:

```powershell
cd C:\Users\LmCas\OneDrive\Documentos\Desarrollo\Maestria\SAVI\Back_End_SAVI
```

Luego inicia el servidor con:

```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

O simplemente:

```powershell
python main.py
```

**NOTA:** El comando cambió de `app.main:app` a `main:app` debido a la nueva estructura del proyecto.

El servidor estará disponible en:
- **API**: http://localhost:8000
- **Documentación Swagger**: http://localhost:8000/docs
- **Documentación ReDoc**: http://localhost:8000/redoc

### Modo producción

```powershell
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 🔐 Credenciales de Prueba

Después de ejecutar `init_db.py`, puedes usar:

### Usuario Administrador
- **Usuario**: `admin`
- **Contraseña**: `admin123`
- **Rol**: admin

### Usuario Cajero
- **Usuario**: `cajero`
- **Contraseña**: `cajero123`
- **Rol**: cashier

## 📡 Probar la API

### 1. Health Check

```powershell
curl http://localhost:8000/health
```

### 2. Login

```powershell
curl -X POST "http://localhost:8000/api/v1/auth/login" `
  -H "Content-Type: application/x-www-form-urlencoded" `
  -d "username=admin&password=admin123"
```

### 3. Obtener productos

```powershell
curl http://localhost:8000/api/v1/products
```

## 🐛 Solución de Problemas

### Error: "Can't connect to MySQL server"

Verifica que:
1. MySQL Server esté ejecutándose
2. Las credenciales en `.env` sean correctas
3. La base de datos `savidb` exista
4. El puerto 3306 esté abierto

```powershell
# Verificar si MySQL está corriendo
Get-Service MySQL*
```

### Error: "Access denied for user 'root'"

Verifica la contraseña en `.env` y asegúrate de que el usuario tenga permisos:

```sql
GRANT ALL PRIVILEGES ON savidb.* TO 'root'@'localhost';
FLUSH PRIVILEGES;
```

### Error: "aiomysql is not installed"

Reinstala las dependencias:

```powershell
pip install -r requirements.txt --force-reinstall
```

### Error: "No module named 'jose'"

Instala python-jose:

```powershell
pip install python-jose[cryptography]
```

### Error: "password cannot be longer than 72 bytes" o problemas con bcrypt

Esto ocurre por incompatibilidad entre versiones de bcrypt y passlib. Solución:

```powershell
# Desinstalar versiones problemáticas
pip uninstall -y bcrypt passlib

# Instalar versiones compatibles
pip install bcrypt==4.0.1 passlib==1.7.4
```

### Error: "ModuleNotFoundError: No module named 'app'"

Esto significa que estás usando comandos antiguos. La estructura del proyecto cambió:
- ❌ Antes: `uvicorn app.main:app`
- ✅ Ahora: `uvicorn main:app`

Solución:
```powershell
# Asegúrate de usar el comando correcto
uvicorn main:app --reload
```

### Puerto 8000 ya en uso

Usa otro puerto:

```powershell
uvicorn main:app --reload --port 8001
```

O detén el proceso que está usando el puerto:

```powershell
# Buscar el proceso que usa el puerto 8000
Get-NetTCPConnection -LocalPort 8000 | Select-Object OwningProcess

# Detener el proceso (reemplaza XXXX con el ID del proceso)
Stop-Process -Id XXXX
```

## 📚 Endpoints Disponibles

### Autenticación
- `POST /api/v1/auth/register` - Registrar usuario
- `POST /api/v1/auth/login` - Iniciar sesión
- `GET /api/v1/auth/me` - Obtener usuario actual

### Productos
- `GET /api/v1/products` - Listar productos
- `GET /api/v1/products/{id}` - Obtener producto
- `POST /api/v1/products` - Crear producto
- `PUT /api/v1/products/{id}` - Actualizar producto
- `DELETE /api/v1/products/{id}` - Eliminar producto

### Clientes
- `GET /api/v1/customers` - Listar clientes
- `GET /api/v1/customers/{id}` - Obtener cliente
- `POST /api/v1/customers` - Crear cliente
- `PUT /api/v1/customers/{id}` - Actualizar cliente
- `DELETE /api/v1/customers/{id}` - Eliminar cliente

### Ventas
- `GET /api/v1/sales` - Listar ventas
- `GET /api/v1/sales/{id}` - Obtener venta
- `POST /api/v1/sales` - Crear venta
- `PUT /api/v1/sales/{id}` - Actualizar venta

## 🔄 Reiniciar Base de Datos

Si necesitas limpiar y reiniciar:

```sql
DROP DATABASE savidb;
CREATE DATABASE savidb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Luego ejecuta nuevamente:

```powershell
python init_db.py
```

## 📝 Próximos Pasos

1. ✅ Backend funcionando en http://localhost:8000
2. ✅ Documentación disponible en http://localhost:8000/docs
3. 🔜 Conectar con el Frontend (http://localhost:5173)
4. 🔜 Implementar más endpoints según necesidades
5. 🔜 Agregar tests

## 🆘 Soporte

Si tienes problemas, revisa:
1. Logs del servidor
2. Documentación de FastAPI: https://fastapi.tiangolo.com
3. Documentación de SQLAlchemy: https://docs.sqlalchemy.org

---

¡Backend SAVI listo para usar! 🎉
