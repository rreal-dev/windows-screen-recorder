
# Screen Recorder App

Screen Recorder App es una aplicación de escritorio para Windows desarrollada en Python, que permite grabar la pantalla junto con el audio del sistema y del micrófono, sincronizados en una sola grabación. Esta aplicación está diseñada para ser intuitiva, discreta y fácil de usar.

## Características

- **Grabación de Pantalla**: Selecciona una de las pantallas disponibles para grabar.
- **Grabación de Audio**: Graba el audio del sistema y del micrófono.
- **Sincronización de Audio y Video**: Sincroniza automáticamente el audio del sistema y del micrófono con la grabación de pantalla.
- **Prueba de Micrófono**: Realiza una prueba de sonido del micrófono antes de la grabación.
- **Selección de FPS**: Permite seleccionar los FPS (15, 30, 60, 120) para la grabación.
- **Selección de Ubicación de Almacenamiento**: Permite seleccionar la ubicación donde se guardarán las grabaciones.
- **Indicador de Tiempo de Grabación**: Muestra un contador de tiempo en formato hh:mm:ss durante la grabación.
- **Logs en Tiempo Real**: Ventana de depuración que muestra todos los logs de la aplicación en tiempo real.
- **Visualización del Cursor**: Captura y muestra la posición del cursor en la grabación.

## Instrucciones de Uso

### Requisitos Previos

- Python 3.6 o superior
- Pip (gestor de paquetes de Python)

### Instalación

1. **Clona el repositorio**:
git clone https://github.com/tu-usuario/screen-recorder.git
cd screen-recorder

2. **Crea un entorno virtual**:
python -m venv venv

3. **Activa el entorno virtual**:
- En Windows:
  ```
  venv\Scripts\activate
  ```
- En macOS/Linux:
  ```
  source venv/bin/activate
  ```

4. **Instala las dependencias**:
pip install -r requirements.txt

### Ejecución de la Aplicación

Para ejecutar la aplicación, asegúrate de que el entorno virtual esté activado y ejecuta el siguiente comando:

python main.py

### Empaquetado de la Aplicación

Si deseas compartir la aplicación como un ejecutable, sigue estos pasos para empaquetarla usando PyInstaller:

1. **Instala PyInstaller**:
pip install pyinstaller

2. **Genera el archivo `.spec`**:
pyinstaller main.py

3. **Modifica el archivo `.spec`** para asegurarte de que los plugins de PyQt5 se incluyan correctamente. Añade la siguiente línea en la sección `datas`:

datas=[
('venv/Lib/site-packages/PyQt5/Qt5/plugins', 'PyQt5/Qt5/plugins')
],

4. **Compila usando el archivo `.spec`**:
pyinstaller main.spec

5. **Compartir el ejecutable**: Después de compilar, encontrarás el ejecutable en la carpeta `dist/main`. Comparte esta carpeta completa, ya que contiene todos los archivos necesarios para la ejecución.

### Uso de la Aplicación

1. **Selecciona una Pantalla**:
- La aplicación mostrará una previsualización de las pantallas disponibles. Haz clic en la pantalla que deseas grabar.

2. **Selecciona un Micrófono**:
- Elige el micrófono desde la lista desplegable. Puedes realizar una prueba de sonido del micrófono antes de iniciar la grabación.

3. **Configura los FPS**:
- Selecciona los FPS deseados para la grabación (15, 30, 60, 120).

4. **Configura la Ubicación de Almacenamiento**:
- Elige la ubicación donde se guardarán las grabaciones. Por defecto, las grabaciones se guardarán en una carpeta llamada "grabaciones".

5. **Iniciar y Detener la Grabación**:
- Haz clic en "Comenzar Grabación" para iniciar la grabación. Durante la grabación, el botón cambiará a "Detener Grabación".
- Un contador de tiempo en formato hh:mm:ss mostrará la duración de la grabación

