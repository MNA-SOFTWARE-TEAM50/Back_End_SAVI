# 🚀 Script de Instalación Automatizada - SAVI Backend

# Este script automatiza la instalación completa del backend de SAVI
# Ejecutar con PowerShell en el directorio Back_End_SAVI

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  SAVI Backend - Instalación Automatizada" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Verificar que estamos en el directorio correcto
$currentDir = Split-Path -Leaf (Get-Location)
if ($currentDir -ne "Back_End_SAVI") {
    Write-Host "❌ Error: Este script debe ejecutarse desde el directorio Back_End_SAVI" -ForegroundColor Red
    Write-Host "   Navega al directorio correcto con: cd Back_End_SAVI" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Directorio correcto verificado" -ForegroundColor Green
Write-Host ""

# Paso 1: Verificar Python
Write-Host "📋 Paso 1/7: Verificando Python..." -ForegroundColor Cyan
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Python no está instalado o no está en el PATH" -ForegroundColor Red
    Write-Host "   Descarga Python desde: https://www.python.org/" -ForegroundColor Yellow
    exit 1
}
Write-Host "   $pythonVersion" -ForegroundColor Green
Write-Host ""

# Paso 2: Crear entorno virtual
Write-Host "📦 Paso 2/7: Creando entorno virtual..." -ForegroundColor Cyan
if (Test-Path "venv") {
    Write-Host "   ⚠️  Entorno virtual ya existe, se omite creación" -ForegroundColor Yellow
} else {
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Error al crear entorno virtual" -ForegroundColor Red
        exit 1
    }
    Write-Host "   ✅ Entorno virtual creado" -ForegroundColor Green
}
Write-Host ""

# Paso 3: Activar entorno virtual
Write-Host "🔌 Paso 3/7: Activando entorno virtual..." -ForegroundColor Cyan
& ".\venv\Scripts\Activate.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error al activar entorno virtual" -ForegroundColor Red
    Write-Host "   Si hay error de permisos, ejecuta:" -ForegroundColor Yellow
    Write-Host "   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Yellow
    exit 1
}
Write-Host "   ✅ Entorno virtual activado" -ForegroundColor Green
Write-Host ""

# Paso 4: Actualizar pip
Write-Host "⬆️  Paso 4/7: Actualizando pip..." -ForegroundColor Cyan
python -m pip install --upgrade pip --quiet
Write-Host "   ✅ pip actualizado" -ForegroundColor Green
Write-Host ""

# Paso 5: Instalar dependencias principales
Write-Host "📚 Paso 5/7: Instalando dependencias principales..." -ForegroundColor Cyan
pip install -r requirements.txt --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error al instalar dependencias" -ForegroundColor Red
    exit 1
}
Write-Host "   ✅ Dependencias principales instaladas" -ForegroundColor Green
Write-Host ""

# Paso 6: Instalar dependencias adicionales
Write-Host "🔐 Paso 6/7: Instalando dependencias adicionales (bcrypt, passlib, python-jose)..." -ForegroundColor Cyan
pip install bcrypt==4.0.1 passlib==1.7.4 --quiet
pip install "python-jose[cryptography]" --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error al instalar dependencias adicionales" -ForegroundColor Red
    exit 1
}
Write-Host "   ✅ bcrypt 4.0.1 instalado" -ForegroundColor Green
Write-Host "   ✅ passlib 1.7.4 instalado" -ForegroundColor Green
Write-Host "   ✅ python-jose instalado" -ForegroundColor Green
Write-Host ""

# Paso 7: Verificar archivo .env
Write-Host "⚙️  Paso 7/7: Verificando configuración..." -ForegroundColor Cyan
if (-not (Test-Path ".env")) {
    Write-Host "   ⚠️  Archivo .env no encontrado" -ForegroundColor Yellow
    if (Test-Path ".env.example") {
        Write-Host "   📄 Copiando .env.example a .env..." -ForegroundColor Cyan
        Copy-Item ".env.example" ".env"
        Write-Host "   ✅ Archivo .env creado" -ForegroundColor Green
    } else {
        Write-Host "   ❌ No se encontró .env ni .env.example" -ForegroundColor Red
    }
} else {
    Write-Host "   ✅ Archivo .env encontrado" -ForegroundColor Green
}
Write-Host ""

# Resumen
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  ✅ Instalación Completada" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📝 Próximos pasos:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Crear la base de datos MySQL:" -ForegroundColor Yellow
Write-Host "   CREATE DATABASE savidb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" -ForegroundColor White
Write-Host ""
Write-Host "2. Inicializar la base de datos:" -ForegroundColor Yellow
Write-Host "   python init_db.py" -ForegroundColor White
Write-Host ""
Write-Host "3. Iniciar el servidor:" -ForegroundColor Yellow
Write-Host "   uvicorn main:app --reload" -ForegroundColor White
Write-Host "   o simplemente:" -ForegroundColor White
Write-Host "   python main.py" -ForegroundColor White
Write-Host ""
Write-Host "4. Acceder a la API:" -ForegroundColor Yellow
Write-Host "   • API: http://localhost:8000" -ForegroundColor White
Write-Host "   • Documentación: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "🔐 Credenciales de prueba:" -ForegroundColor Cyan
Write-Host "   • Admin: admin / admin123" -ForegroundColor White
Write-Host "   • Cajero: cajero / cajero123" -ForegroundColor White
Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "¡Backend listo para usar! 🎉" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Cyan
