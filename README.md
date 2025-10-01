# SAVI - Backend API

Backend desarrollado con FastAPI para el Sistema de Administración de Ventas e Inventario.

## 🚀 Tecnologías

- **FastAPI** - Framework web moderno y rápido
- **Python 3.11+** - Lenguaje de programación
- **SQLAlchemy** - ORM para base de datos
- **Alembic** - Migraciones de base de datos
- **Pydantic** - Validación de datos
- **PostgreSQL/SQLite** - Base de datos
- **JWT** - Autenticación con tokens

## 📁 Estructura del Proyecto

```
Back_End_SAVI/
├── app/
│   ├── api/
│   │   └── v1/           # Endpoints API versión 1
│   │       ├── products.py
│   │       ├── sales.py
│   │       ├── customers.py
│   │       └── users.py
│   ├── core/             # Configuración central
│   │   ├── config.py
│   │   └── security.py
│   ├── db/               # Base de datos
│   │   ├── base.py
│   │   └── session.py
│   ├── models/           # Modelos SQLAlchemy
│   │   ├── product.py
│   │   ├── sale.py
│   │   ├── customer.py
│   │   └── user.py
│   ├── schemas/          # Schemas Pydantic
│   │   ├── product.py
│   │   ├── sale.py
│   │   ├── customer.py
│   │   └── user.py
│   ├── services/         # Lógica de negocio
│   └── main.py           # Punto de entrada
├── alembic/              # Migraciones
├── tests/                # Tests
├── requirements.txt      # Dependencias
├── .env                  # Variables de entorno
└── README.md
```

## 🛠️ Instalación

### 1. Crear entorno virtual

```bash
python -m venv venv
```

### 2. Activar entorno virtual

**Windows (PowerShell):**
```bash
.\venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```bash
.\venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

```bash
copy .env.example .env
```

Editar `.env` con tus configuraciones.

### 5. Inicializar base de datos

```bash
# Crear las tablas
python -m app.db.init_db
```

## 🚀 Uso

### Desarrollo

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

O simplemente:

```bash
python main.py
```

La API estará disponible en: `http://localhost:8000`

**NOTA:** El comando cambió de `app.main:app` a `main:app` debido a la reestructuración del proyecto.

### Documentación API

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Producción

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📚 Endpoints API

### Autenticación
- `POST /api/v1/auth/login` - Iniciar sesión
- `POST /api/v1/auth/register` - Registrar usuario

### Productos
- `GET /api/v1/products` - Listar productos
- `GET /api/v1/products/{id}` - Obtener producto
- `POST /api/v1/products` - Crear producto
- `PUT /api/v1/products/{id}` - Actualizar producto
- `DELETE /api/v1/products/{id}` - Eliminar producto

### Ventas
- `GET /api/v1/sales` - Listar ventas
- `GET /api/v1/sales/{id}` - Obtener venta
- `POST /api/v1/sales` - Crear venta
- `PUT /api/v1/sales/{id}` - Actualizar venta

### Clientes
- `GET /api/v1/customers` - Listar clientes
- `GET /api/v1/customers/{id}` - Obtener cliente
- `POST /api/v1/customers` - Crear cliente
- `PUT /api/v1/customers/{id}` - Actualizar cliente

### Usuarios
- `GET /api/v1/users/me` - Obtener usuario actual
- `PUT /api/v1/users/me` - Actualizar perfil

## 🧪 Testing

```bash
pytest
```

Con cobertura:
```bash
pytest --cov=app tests/
```

## 🔒 Seguridad

- Autenticación JWT
- Contraseñas hasheadas con bcrypt
- CORS configurado
- Validación de datos con Pydantic

## 📝 Variables de Entorno

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `APP_NAME` | Nombre de la aplicación | SAVI API |
| `DEBUG` | Modo debug | True |
| `DATABASE_URL` | URL de la base de datos | sqlite:///./savi.db |
| `SECRET_KEY` | Clave secreta JWT | your-secret-key |
| `CORS_ORIGINS` | Orígenes permitidos CORS | http://localhost:5173 |

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto es privado y confidencial.

## 👥 Equipo

MNA-SOFTWARE-TEAM50
