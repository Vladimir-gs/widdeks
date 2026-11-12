# Widdeks - Reloj y Panel de Escritorio

Widdeks es una aplicación de escritorio para Windows que muestra un reloj personalizable y un panel con acceso rápido a aplicaciones, controles de medios, volumen, brillo y estado de batería. La aplicación se ejecuta en la pantalla y se puede arrastrar y redimensionar según tus preferencias.

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

   *Alternativamente, puedes ejecutar el script desde el directorio de widdeks:*

   ```powershell
   cd clock-widget
   .\install.ps1
   ```

2. **Qué hace el instalador**
   - Copia `widdeks.py` y las fuentes a `%LOCALAPPDATA%\Programs\Widdeks`
   - Configura el inicio automático en el registro de Windows
   - Crea un acceso directo en el menú Inicio etiquetado como "Widdeks"
   - Elimina la instalación anterior "Reloj Widget" si existe
   - Inicia la aplicación automáticamente

3. **Primer lanzamiento**
   Al finalizar la instalación, widdeks se iniciará automáticamente. Deberías ver el reloj y el panel en tu escritorio.

## Uso básico

### Control de la aplicación

- **Clic derecho en el reloj/panel**: Abre un menú con opciones de configuración
- **Arrastrar**: Mueve el reloj o panel a cualquier posición de tu pantalla
- **Grip (esquina inferior derecha)**: Arrastra para redimensionar el reloj
- **Rueda de mouse sobre el reloj**: Ajusta el tamaño de la fuente

### Configuración del reloj

Haz clic derecho sobre el reloj para acceder a estas opciones:

- **Formato**: Cambiar entre 24h y 12h
- **Orientación**: Vertical (apilado) u Horizontal
- **Segundos**: Mostrar u ocultar los segundos
- **Color del texto**: Selecciona un nuevo color
- **Grosor de fuente**: Light, Regular, Medium, SemiBold, Bold
- **Agrandar/Reducir**: Ajusta el tamaño con los botones del menú

### Configuración del panel

Haz clic derecho sobre el panel para:

- **Ocultar panel**: Ocultar/mostrar el panel
- **Salir**: Cerrar la aplicación completamente

### Accesos directos del panel

El panel incluye botones para:
- Aplicaciones configuradas (Chrome, VS Code, Discord, Terminal, etc.)
- Controles de medios (anterior, play/pause, siguiente)
- Control de volumen (subir/bajar)
- Control de brillo de pantalla
- Información de batería

## Desinstalación

Para desinstalar widdeks completamente:

1. Ejecuta el script de desinstalación:

   ```powershell
   .\clock-widget\desinstalar.bat
   ```

2. Esto hará lo siguiente:
   - Cierra todos los procesos de widdeks
   - Elimina la entrada del registro de inicio automático
   - Elimina el acceso directo del menú Inicio
   - Remueve los archivos de instalación de `%LOCALAPPDATA%\Programs\Widdeks`
   - También remueve la carpeta anterior `RelojWidget` si existe

## Configuración manual (opcional)

Puedes personalizar la configuración directamente editando los archivos JSON:

- **`clock_config.json`**: Configura el reloj (tamaño, peso, color, formato, segundos, orientación)
- **`panel_config.json`**: Configura el panel (posición, accesos directos)

Estos archivos se encuentran en la carpeta de instalación o en `%LOCALAPPDATA%\Programs\Widdeks\`.

## Notas importantes

- La primera vez que ejecutes la aplicación, Windows puede pedir permiso para que ejecute scripts de PowerShell. Asegúrate de permitirla.
- Si deseas desactivar el inicio automático, ve a **Administrador de tareas > Más detalles > Pestaña Inicio** y desactiva la entrada "Widdeks".
- La aplicación está diseñada para Windows y usa bibliotecas nativas de Windows (pycaw para audio, winrt para medios).
- Para problemas con el brillo o volumen, asegúrate de tener los controladores necesarios de tu fabricante de dispositivo.