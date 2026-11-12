# Widdeks - Reloj y Panel de Escritorio

![Widdeks reloj](clock-widget/screenshots/click-hora.png =300x)

Widdeks es una aplicación de escritorio para Windows que muestra un reloj personalizable y un panel con acceso rápido a aplicaciones, controles de medios, volumen, brillo y estado de batería. La aplicación se ejecuta en la pantalla y se puede arrastrar y redimensionar según tus preferencias.

> **Consejo:** Las capturas de pantalla se encuentran en la carpeta `clock-widget/screenshots/`. Puedes agregar más imágenes allí y referenciarlas con la sintaxis Markdown estándar.

## Instalación

### Requisitos previos
- Windows 10/11
- Python 3.x instalado
- `pythonw.exe` debe estar disponible en tu PATH

### Pasos de instalación

1. **Ejecutar el instalador PowerShell**
   Abre PowerShell como administrador y ejecuta:

   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\clock-widget\install.ps1
   ```

   *Alternativamente, desde la carpeta clock-widget:*

   ```powershell
   cd clock-widget
   .\install.ps1
   ```

2. **Qué hace el instalador**
   - Copia `widdeks.py` y las fuentes a `%LOCALAPPDATA%\Programs\Widdeks`
   - Configura el inicio automático en el registro de Windows bajo "Widdeks"
   - Crea un acceso directo en el menú Inicio con el nombre "Widdeks"
   - Elimina la instalación anterior "Reloj Widget" si existe
   - Inicia la aplicación automáticamente

3. **Primer lanzamiento**
   Al terminar, verás un reloj digital y un panel en tu escritorio. La aplicación debería abrirse automáticamente.

## Uso básico

### Interfaz de la aplicación

Al iniciar, verás dos elementos principales en tu escritorio:

- **Reloj**: Un reloj digital en el lado derecho (por defecto) que muestra la hora
- **Panel**: Una barra inferior con acceso a aplicaciones, controles y estado del sistema

### Interacción con el reloj

**Clic derecho sobre el reloj** → Abre un menú con estas opciones de configuración:

| Opción | Descripción |
|--------|-------------|
| **Formato** | Alterna entre 24 horas y 12 horas (AM/PM) |
| **Orientación** | Cambia entre disposición vertical (apilada) u horizontal |
| **Segundos** | Muestra u oculta los segundos en el reloj |
| **Color del texto** | Abre un selector de colores para cambiar el color de la hora |
| **Grosor de fuente** | Elige entre: Light, Regular, Medium, SemiBold, Bold |
| **Agrandar + / Reducir -** | Ajusta el tamaño de la fuente usando los botones del menú |
| **Rueda de mouse** | Desplazando la rueda sobre el reloj, aumentas o disminuyes el tamaño |

**Arrastrar el reloj**: Haz clic y arrastra en cualquier parte del reloj para moverlo a cualquier posición de la pantalla.

**Grip (esquina inferior derecha)**: Un pequeño cuadro en la esquina que puedes arrastrar para redimensionar el reloj manualmente.

**Rueda de mouse sobre el reloj**: Desplázala hacia adelante para hacer el reloj más grande, hacia atrás para hacerlo más pequeño.

### Interacción con el panel

**Clic derecho sobre el panel** → Menú con:

- **Ocultar panel**: Oculta o muestra el panel de escritorio
- **Salir**: Cierra completamente la aplicación

### Accesos directos del panel

El panel incluye secciones interactivas:

**Aplicaciones rápidas**: Botones para lanzar programas configurados (Chrome, VS Code, Discord, Terminal, Explorador, Ajustes, Calculadora, Notas). Cada botón muestra el icono del programa.

**Controles de medios**: Si estás reproduciendo música o video:
- **Anterior**: Canción/anterior
- **Play/Pause**: Reproducción/pausa
- **Siguiente**: Siguiente canción

**Control de volumen**: 
- Botones + y - para subir/bajar el volumen
- Muestra el nivel actual de volumen

**Brillo de pantalla**:
- Botones + y - para ajustar el brillo
- Muestra el nivel actual de brillo

**Batería**: Icono de batería con estado (cargando, en batería, porcentaje)

## Configuración manual (opcional)

Los archivos de configuración se guardan en formato JSON y se pueden editar directamente:

- **`clock_config.json`**: Configura el reloj
  - `x`, `y`: Posición en la pantalla
  - `size`: Tamaño del reloj (150 por defecto)
  - `weight`: Grosor de la fuente (Medium por defecto)
  - `hour24`: true para 24h, false para 12h
  - `seconds`: Mostrar segundos
  - `vertical`: true para vertical, false para horizontal
  - `color`: Color del texto (ej. "#ffffff" blanco)

- **`panel_config.json`**: Configura el panel
  - `x`, `y`: Posición
  - `shortcuts`: Array de accesos directos a aplicaciones

Estos archivos están en `%LOCALAPPDATA%\Programs\Widdeks\` o en la carpeta de instalación.

## Desinstalación

Para desinstalar widdeks completamente:

```powershell
.\clock-widget\desinstalar.bat
```

Esto hará lo siguiente:
- Cerrará todos los procesos de widdeks
- Eliminará la entrada del registro de inicio automático ("Widdeks")
- Removerá el acceso directo del menú Inicio
- Borrará los archivos de `%LOCALAPPDATA%\Programs\Widdeks\`
- También removerá la carpeta anterior `RelojWidget` si existe

## Notas importantes

- **Primera ejecución**: Windows puede mostrar un aviso sobre scripts de PowerShell. Selecciona "More info" y luego "Run anyway" para permitir la ejecución.
- **Auto-start**: Si deseas desactivar el inicio automático, ve a **Administrador de tareas** > **Más detalles** > pestaña **Inicio** y desactiva la entrada "Widdeks".
- **Compatibilidad**: La aplicación está diseñada para Windows y usa bibliotecas nativas (pycaw para audio, winrt para controles de medios).
- **Solución de problemas**: Si el brillo o volumen no responden, verifica que tengas instalados los controladores adecuados de tu fabricante de laptop/desktop.
- **Personalización avanzada**: Edita directamente los archivos JSON si quieres configuraciones que no están disponibles en el menú clic-derecho.

---

*¿Necesitas agregar más secciones o detalles específicos?*