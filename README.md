# FitControl — Prototipo

Aplicación web para la gestión de un gimnasio, desarrollada con Python, Django y MariaDB.

Incluye gestión de socios, entrenadores, membresías, pagos, clases, reservas, asistencias y reportes. Dispone de funciones diferenciadas para administrador, socio y entrenador.

## Requisitos

- Python 3.12 o posterior compatible con las dependencias.
- MariaDB instalado y en ejecución.
- Una base de datos independiente para el prototipo.

## Instalación en Windows

1. Descargar el repositorio mediante **Code → Download ZIP** y descomprimirlo.
2. Abrir una terminal PowerShell dentro de la carpeta `FitControlPrototipo` que contiene `manage.py`.
3. Crear un entorno virtual e instalar las dependencias:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Configuración de MariaDB

Crear una base vacía desde HeidiSQL o mediante SQL:

```sql
CREATE DATABASE fitcontrolprototipo
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
```

En la misma terminal PowerShell, configurar los datos de conexión de su instalación:

```powershell
$env:DB_NAME = "fitcontrolprototipo"
$env:DB_USER = "SU_USUARIO"
$env:DB_PASSWORD = "SU_CONTRASEÑA"
$env:DB_HOST = "127.0.0.1"
$env:DB_PORT = "3306"
```

Reemplazar `SU_USUARIO` y `SU_CONTRASEÑA` por las credenciales locales de MariaDB.

## Preparar e iniciar el prototipo

Ejecutar desde la carpeta que contiene `manage.py`:

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py cargar_demo --password 'FitControlDemo2026!'
.\.venv\Scripts\python.exe manage.py runserver 8016
```

Abrir en el navegador:

http://127.0.0.1:8016/

Mantener la terminal y MariaDB en ejecución mientras se utiliza la aplicación.

## Cuentas de demostración

Después de cargar la demostración en una base nueva:

| Rol | Correo | Contraseña |
|---|---|---|
| Administrador | admin@fitcontrol.demo | FitControlDemo2026! |
| Socio | socio@fitcontrol.demo | FitControlDemo2026! |
| Entrenador | entrenador@fitcontrol.demo | FitControlDemo2026! |

Estas cuentas contienen datos ficticios y son exclusivamente para pruebas locales.

Si se utiliza otra contraseña en `cargar_demo`, ingresar con esa contraseña. El comando conserva las contraseñas de las cuentas existentes.

El administrador de la aplicación no es un superusuario del panel administrativo de Django.

## Alcance

El prototipo funciona localmente y registra pagos de manera administrativa; no procesa transacciones bancarias.

El repositorio contiene el código fuente. No incluye la base de datos del equipo de desarrollo: las migraciones y el comando `cargar_demo` permiten preparar una instalación independiente.
