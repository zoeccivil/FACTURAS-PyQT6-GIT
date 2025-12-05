# Facturas Pro - Sistema de Gestión de Facturas

Sistema completo de gestión de facturación con interfaz moderna, integración con Firebase y copias de seguridad automáticas.

## 🆕 Nuevas Características

### 1. Interfaz Moderna (Dashboard SaaS)

La aplicación ahora incluye una interfaz completamente rediseñada con un estilo moderno y profesional:

- **Sidebar de navegación** con selector de empresas
- **4 tarjetas KPI** mostrando métricas en tiempo real:
  - Total Ingresos (con ITBIS)
  - Total Gastos (con ITBIS)
  - ITBIS Neto (diferencia)
  - A Pagar Estimado
- **Tabla de transacciones moderna** con:
  - Badges de color para tipo de transacción
  - Filtros rápidos (Todos/Ingresos/Gastos)
  - Ordenamiento y búsqueda
- **Filtros por mes y año**
- **Diseño responsive** y profesional

### 2. Integración con Firebase

#### Configuración de Firebase

1. Ve a **Herramientas → Configuración Firebase**
2. Selecciona tu archivo JSON de credenciales de servicio
3. El sistema autocompletará el Project ID
4. Especifica el bucket de Storage (ej: `mi-proyecto.appspot.com`)
5. Prueba la conexión antes de guardar

#### Migración de Datos

1. Configura Firebase primero
2. Ve a **Herramientas → Migrador de Datos (SQLite → Firebase)**
3. Opciones:
   - ✅ Limpiar colecciones antes de migrar (elimina datos existentes)
   - 📊 Progreso en tiempo real
   - 📝 Logs detallados con códigos de color
   - ⏸️ Cancelación segura en cualquier momento

**Colecciones migradas:**
- `companies` - Empresas
- `invoices` - Facturas (con subcollección `items`)
- `items` - Artículos de facturas

### 3. Sistema de Copias de Seguridad

#### Copias Automáticas

- Las copias se crean con timestamp: `facturas_db_backup_20231205_143022.db`
- Política de retención: **30 días automáticos**
- Limpieza automática de copias antiguas

#### Gestión Manual

**Herramientas → Gestionar Copias de Seguridad:**

- ✅ **Crear copia** nueva en cualquier momento
- 🔄 **Restaurar** cualquier copia (con backup pre-restauración)
- 🗑️ **Eliminar** copias individuales
- 🧹 **Limpiar** copias antiguas (>30 días)
- 📊 Ver tamaño y antigüedad de cada copia

## 📦 Instalación

### Requisitos

```bash
pip install -r requirements.txt
```

**Dependencias principales:**
- PyQt6 >= 6.4.0
- pandas >= 1.5.0
- firebase-admin >= 6.0.0
- qtawesome >= 1.2.0 (opcional, para iconos)
- openpyxl, fpdf, Pillow, pypdf

### Configuración Inicial

1. **Primera ejecución:**
   ```bash
   python main_qt.py
   ```

2. **Seleccionar base de datos:**
   - Crea o selecciona tu archivo `.db`
   - La ruta se guardará en `config.json`

3. **Configurar Firebase (opcional):**
   - Descarga credenciales JSON desde Firebase Console
   - Configura en **Herramientas → Configuración Firebase**

## 🎨 Interfaz de Usuario

### UI Moderna (Por Defecto)

La aplicación usa por defecto la interfaz moderna. Características:

- **Sidebar oscuro** (#1E293B) con navegación
- **Área de contenido clara** (#F8F9FA)
- **Tarjetas KPI** con métricas en tiempo real
- **Tabla moderna** con badges de color
- **Botones primarios** en azul (#3B82F6)

### UI Clásica (Opcional)

Para usar la UI clásica, edita `config.json`:

```json
{
  "use_modern_ui": false,
  "database_path": "ruta/a/tu/database.db"
}
```

## 🔧 Menú Herramientas

El nuevo menú **Herramientas** incluye:

1. **Migrador de Datos (SQLite → Firebase)**
   - Migración completa con progreso visual
   - Logs en tiempo real
   - Estadísticas por colección
   - Cancelación segura

2. **Configuración Firebase**
   - Selección de credenciales
   - Validación automática
   - Prueba de conexión

3. **Gestionar Copias de Seguridad**
   - Crear/Restaurar/Eliminar copias
   - Retención automática de 30 días
   - Vista de todas las copias disponibles

4. **Gestionar Empresas**
   - Añadir/Editar/Eliminar empresas
   - Configuración de RNC y dirección

## 📊 Funcionalidades Principales

### Gestión de Facturas

- **Facturas Emitidas (Ingresos)**
  - Registro completo con items
  - Cálculo automático de ITBIS
  - Soporte multi-moneda

- **Facturas de Gastos**
  - Control de gastos deducibles
  - ITBIS recuperable
  - Categorización

### Reportes

- **Reporte Mensual**
  - PDF profesional con resumen
  - Incluye anexos de comprobantes
  - Estadísticas completas

- **Reporte por Tercero**
  - Historial completo por RNC
  - Total de ingresos y gastos
  - Análisis de relación comercial

### Cálculo de Impuestos

- **Calculadora Avanzada**
  - Selección de período
  - Retenciones automáticas
  - Generación de reportes PDF
  - Guardado de cálculos

## 🗂️ Estructura de Archivos

```
FACTURAS-PyQT6-GIT/
├── main_qt.py                    # Punto de entrada principal
├── modern_gui.py                 # UI moderna (dashboard)
├── app_gui_qt.py                 # UI clásica
├── logic_qt.py                   # Controlador de lógica de negocio
├── config_manager.py             # Gestión de configuración
├── firebase_client.py            # Cliente Firebase (Firestore/Storage)
├── firebase_config_dialog.py     # Diálogo de configuración Firebase
├── migration_dialog.py           # Diálogo de migración de datos
├── backup_manager.py             # Sistema de copias de seguridad
├── backup_dialog.py              # UI de gestión de copias
├── requirements.txt              # Dependencias Python
├── config.json                   # Configuración de la aplicación
├── backups/                      # Carpeta de copias de seguridad
└── [otros archivos de ventanas]
```

## 🔐 Seguridad

### Firebase

- Las credenciales se almacenan localmente en `config.json`
- **NO** subir `config.json` ni archivos JSON de credenciales a repositorios públicos
- Usar variables de entorno en producción

### Copias de Seguridad

- Las copias incluyen **todos** los datos de la aplicación
- Almacenar en ubicación segura
- Política de retención de 30 días
- Backup automático antes de restaurar

## 🚀 Uso Rápido

### Crear Nueva Factura

1. Selecciona empresa en el sidebar
2. Click en **"+ Nueva Factura"** (header) o botón en sidebar
3. Completa datos: fecha, número, tercero, items
4. El sistema calcula automáticamente ITBIS y total
5. Guardar

### Ver Resumen del Mes

1. Usa los filtros de Mes/Año en la parte superior
2. Click **"Aplicar Filtro"**
3. Las tarjetas KPI se actualizan automáticamente
4. La tabla muestra solo transacciones del período

### Generar Reporte

1. **Reportes → Reporte Mensual**
2. Selecciona mes y año
3. Elige formato (PDF/Excel)
4. El PDF incluye automáticamente anexos de comprobantes

### Migrar a Firebase

1. **Herramientas → Configuración Firebase** (primera vez)
2. **Herramientas → Migrador de Datos**
3. Opcional: marcar "Limpiar colecciones"
4. Click **"Iniciar Migración"**
5. Esperar a que termine (ver progreso en tiempo real)

## 🐛 Solución de Problemas

### Error al iniciar la aplicación (ModuleNotFoundError)

Si ves un error como `ModuleNotFoundError: No module named 'PyQt6'` o similar:

1. **Instala todas las dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Verifica la instalación con el script de prueba:**
   ```bash
   python test_imports.py
   ```
   Este script verificará que todos los módulos necesarios estén instalados correctamente.

3. **Si el problema persiste:**
   - Asegúrate de usar Python 3.8 o superior: `python --version`
   - Considera usar un entorno virtual:
     ```bash
     python -m venv venv
     # Windows:
     venv\Scripts\activate
     # Linux/Mac:
     source venv/bin/activate
     
     pip install -r requirements.txt
     python main_qt.py
     ```

### Firebase no conecta

1. Verifica que el archivo JSON sea de tipo `service_account`
2. Comprueba que el bucket existe en Firebase Console
3. Revisa permisos del service account
4. Usa **"Probar Conexión"** en la configuración

### Error al restaurar copia

1. Cierra la aplicación completamente
2. Restaura la copia manualmente copiando el archivo
3. Reinicia la aplicación

### UI no se ve moderna

1. Verifica `config.json`: debe tener `"use_modern_ui": true`
2. Reinstala dependencias: `pip install -r requirements.txt`
3. Reinicia la aplicación

## 📝 Notas de Desarrollo

### Agregar Nueva Funcionalidad

1. La lógica de negocio va en `logic_qt.py`
2. La UI moderna en `modern_gui.py`
3. La UI clásica en `app_gui_qt.py`
4. Mantener ambas UIs sincronizadas

### Firebase vs SQLite

- **SQLite**: Base de datos local, rápida, ideal para desarrollo
- **Firebase**: Cloud, sincronización, acceso multi-dispositivo
- **Recomendación**: Usar ambas (SQLite para backup, Firebase para datos activos)

## 📄 Licencia

[Especificar licencia del proyecto]

## 👥 Contribuciones

[Instrucciones para contribuir]

## 📞 Soporte

Para reportar problemas o sugerir mejoras:
- Crear un issue en GitHub
- [Otros métodos de contacto]

---

**Facturas Pro** - Sistema profesional de gestión de facturación
Versión 2.0 con Firebase y UI Moderna
