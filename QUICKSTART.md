# Guía de Inicio Rápido - Facturas Pro

## 🚀 Instalación en 5 Minutos

### 1. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 2. Ejecutar la Aplicación

```bash
python main_qt.py
```

### 3. Configuración Inicial

Al ejecutar por primera vez:

1. **Seleccionar/Crear Base de Datos**
   - Se abrirá un diálogo para seleccionar tu archivo `.db`
   - O crea uno nuevo: `facturas_db.db`

2. **Crear Primera Empresa**
   - Menú: **Herramientas → Gestionar Empresas**
   - Click **"Nuevo"**
   - Completa: Nombre, RNC, Dirección
   - Click **"Guardar Cambios"**

3. **¡Listo para usar!**

## 📋 Primeros Pasos

### Registrar tu Primera Factura

1. Asegúrate de tener una empresa seleccionada (sidebar izquierdo)
2. Click en **"+ Nueva Factura"** (botón azul arriba a la derecha)
3. Completa:
   - Fecha de la factura
   - Número de factura (NCF)
   - Tercero/Cliente (RNC y nombre)
   - Moneda
   - Items (descripción, cantidad, precio)
4. El sistema calcula automáticamente:
   - Subtotal
   - ITBIS (18%)
   - Total
5. Click **"Guardar"**

### Ver el Dashboard

El dashboard muestra automáticamente:

- **Total Ingresos**: Suma de todas las facturas emitidas
- **Total Gastos**: Suma de todas las facturas de gastos
- **ITBIS Neto**: Diferencia entre ITBIS cobrado y pagado
- **A Pagar**: Estimado de impuestos a pagar

### Filtrar por Período

1. Usa los dropdowns de **Mes** y **Año**
2. Click **"Aplicar Filtro"**
3. El dashboard se actualiza mostrando solo ese período

## 🔥 Configurar Firebase (Opcional)

### ¿Por qué usar Firebase?

- ☁️ Datos en la nube
- 📱 Acceso desde múltiples dispositivos
- 🔄 Sincronización automática
- 💾 Backup en la nube

### Configuración

1. **Obtener Credenciales de Firebase:**
   - Ve a [Firebase Console](https://console.firebase.google.com)
   - Selecciona tu proyecto (o crea uno nuevo)
   - Ve a **Configuración del Proyecto → Cuentas de Servicio**
   - Click **"Generar nueva clave privada"**
   - Guarda el archivo JSON descargado

2. **Configurar en la Aplicación:**
   - Menú: **Herramientas → Configuración Firebase**
   - Click **"Examinar"** y selecciona el archivo JSON
   - El sistema autocompletar el Project ID
   - En Bucket, pon: `tu-proyecto-id.appspot.com`
   - Click **"Probar Conexión"**
   - Si todo está OK, click **"Guardar"**

3. **Migrar Datos:**
   - Menú: **Herramientas → Migrador de Datos**
   - (Opcional) Marca "Limpiar colecciones" si empiezas desde cero
   - Click **"Iniciar Migración"**
   - Espera a que termine (ver progreso en pantalla)

## 💾 Copias de Seguridad

### Automáticas

- El sistema guarda copias automáticamente
- Se eliminan copias con más de 30 días
- Ubicación: carpeta `backups/`

### Manuales

1. **Crear Copia:**
   - Menú: **Herramientas → Gestionar Copias de Seguridad**
   - Click **"Crear Nueva Copia"**

2. **Restaurar Copia:**
   - Selecciona la copia en la tabla
   - Click **"Restaurar Seleccionada"**
   - **Importante:** Reinicia la aplicación después

## 📊 Generar Reportes

### Reporte Mensual

1. Menú: **Reportes → Reporte Mensual**
2. Selecciona mes y año
3. Elige formato:
   - **PDF**: Incluye anexos de comprobantes
   - **Excel**: Para análisis con tablas dinámicas
4. Click **"Generar"**

### Reporte por Cliente/Proveedor

1. Menú: **Reportes → Reporte por Cliente/Proveedor**
2. Busca por nombre o RNC
3. Selecciona de la lista
4. Click **"Generar Reporte"**
5. Ver historial completo de transacciones

## 🧮 Calcular Impuestos

### Calculadora Simple

1. Ve a **Calc. Impuestos** (sidebar)
2. Selecciona rango de fechas
3. El sistema calcula:
   - ITBIS a pagar
   - Retenciones aplicables
   - Total final
4. Puedes guardar el cálculo para referencia

## ⌨️ Atajos de Teclado

(Por implementar - sugerencias bienvenidas)

## 🆘 Problemas Comunes

### "No se puede conectar a Firebase"

**Solución:**
1. Verifica tu conexión a internet
2. Revisa que el archivo JSON sea correcto
3. Confirma permisos en Firebase Console

### "Error al cargar empresa"

**Solución:**
1. Verifica que existe al menos una empresa
2. Menú: **Herramientas → Gestionar Empresas**
3. Crea una nueva si es necesario

### "La UI se ve diferente"

**Solución:**
- Por defecto usa la UI moderna
- Para cambiar a UI clásica:
  - Edita `config.json`
  - Cambia `"use_modern_ui": false`

## 📚 Recursos Adicionales

- **README.md**: Documentación completa
- **requirements.txt**: Lista de dependencias
- **Código fuente**: Comentado y documentado

## 💡 Consejos Pro

1. **Usa la búsqueda de terceros**: Al registrar facturas, empieza a escribir el RNC o nombre y el sistema autocompletará

2. **Aprovecha los filtros**: La tabla de transacciones tiene filtros rápidos (Todos/Ingresos/Gastos)

3. **Exporta regularmente**: Genera reportes mensuales y guárdalos para tu contador

4. **Haz copias antes de cambios grandes**: Antes de migraciones o cambios importantes

5. **Revisa el ITBIS Neto**: Mantén un ojo en esta métrica para evitar sorpresas al declarar

## 🎯 Próximos Pasos

1. ✅ Registra todas tus facturas del mes actual
2. ✅ Configura Firebase si quieres sync en la nube
3. ✅ Genera tu primer reporte mensual
4. ✅ Explora la calculadora de impuestos
5. ✅ Personaliza según tus necesidades

---

**¿Necesitas ayuda?** Consulta el README.md completo o abre un issue en GitHub.

¡Bienvenido a Facturas Pro! 🎉
