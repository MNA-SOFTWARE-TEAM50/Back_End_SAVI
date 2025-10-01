# 📝 Cambios Importantes en la Estructura del Proyecto

## ⚠️ IMPORTANTE: Lee esto si actualizaste desde una versión anterior

---

## 🔄 Reestructuración del Proyecto (Octubre 2025)

### ¿Qué cambió?

**ANTES:**
```
Back_End_SAVI/
└── app/
    ├── api/
    ├── core/
    ├── db/
    ├── models/
    ├── schemas/
    └── main.py
```

**AHORA:**
```
Back_End_SAVI/
├── api/
├── core/
├── db/
├── models/
├── schemas/
└── main.py
```

### ¿Por qué?

- ✅ **Más simple**: Todo el código está directamente en la raíz
- ✅ **Menos anidamiento**: No hay carpeta `app/` innecesaria
- ✅ **Importaciones más limpias**: `from models.user` en vez de `from app.models.user`
- ✅ **Mejor para el desarrollo**: Estructura más plana y fácil de navegar

---

## 🔧 Cambios Necesarios

### 1. Comando para iniciar el servidor

**❌ Comando ANTIGUO (NO USAR):**
```powershell
uvicorn app.main:app --reload
```

**✅ Comando NUEVO (USAR AHORA):**
```powershell
uvicorn main:app --reload
```

O simplemente:
```powershell
python main.py
```

### 2. Importaciones en el código

Si tienes código personalizado, actualiza las importaciones:

**❌ ANTES:**
```python
from app.models.user import User
from app.core.config import settings
from app.db.session import get_db
```

**✅ AHORA:**
```python
from models.user import User
from core.config import settings
from db.session import get_db
```

### 3. Variables de entorno

El archivo `.env` se mantiene igual, no hay cambios necesarios.

---

## 🐛 Solución de Problemas

### Error: "ModuleNotFoundError: No module named 'app'"

**Causa:** Estás usando comandos o código antiguo.

**Solución:**
1. Usa `uvicorn main:app` en vez de `uvicorn app.main:app`
2. Actualiza las importaciones en tu código (quita `app.` del inicio)

### Error: "No module named 'jose'"

**Causa:** Falta instalar python-jose.

**Solución:**
```powershell
pip install python-jose[cryptography]
```

### Error: "password cannot be longer than 72 bytes"

**Causa:** Incompatibilidad entre versiones de bcrypt y passlib.

**Solución:**
```powershell
pip uninstall -y bcrypt passlib
pip install bcrypt==4.0.1 passlib==1.7.4
```

---

## 📦 Dependencias Actualizadas

Se agregaron versiones específicas para evitar conflictos:

```powershell
# Versiones específicas necesarias
pip install bcrypt==4.0.1
pip install passlib==1.7.4
pip install python-jose[cryptography]
```

Estas se instalan automáticamente si sigues la guía de instalación actualizada.

---

## ✅ Checklist de Actualización

Si estás actualizando desde una versión anterior:

- [ ] Eliminar carpeta `app/` antigua (si existe)
- [ ] Actualizar comando de inicio: `uvicorn main:app --reload`
- [ ] Reinstalar dependencias:
  ```powershell
  pip install bcrypt==4.0.1 passlib==1.7.4
  pip install python-jose[cryptography]
  ```
- [ ] Verificar que el servidor inicie correctamente
- [ ] Probar endpoints en http://localhost:8000/docs

---

## 📚 Documentación Actualizada

Toda la documentación ha sido actualizada:

- ✅ [INSTALL.md](./INSTALL.md) - Guía de instalación completa
- ✅ [README.md](./README.md) - Información general del proyecto
- ✅ [../QUICK_START.md](../QUICK_START.md) - Inicio rápido Frontend + Backend
- ✅ [../README.md](../README.md) - README principal del proyecto

---

## 🆘 ¿Necesitas ayuda?

1. Revisa la [Guía de Instalación](./INSTALL.md) actualizada
2. Consulta la sección de "Solución de Problemas" en INSTALL.md
3. Verifica que estés usando los comandos correctos (sin `app.`)

---

## 📅 Historial de Cambios

### Versión 2.0 (Octubre 2025)
- ✨ Reestructuración completa del proyecto
- ✨ Eliminada carpeta `app/` innecesaria
- 🔧 Comandos simplificados
- 📦 Dependencias actualizadas con versiones específicas
- 📝 Documentación completamente actualizada

### Versión 1.0 (Inicial)
- 🎉 Lanzamiento inicial del backend
- 🔐 Sistema de autenticación JWT
- 📊 CRUD completo de productos, ventas y clientes
- 🗄️ Integración con MySQL

---

**¡La nueva estructura está lista para usar!** 🚀

Para instalación desde cero, sigue [INSTALL.md](./INSTALL.md).
