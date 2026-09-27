# Ruleta de Nombres - Casino Edition (Pygame)

Ruleta de sorteo con **nombres personalizables**, estilo casino:

- Agrega y quita nombres desde la propia interfaz (caja de texto + botón
  "Agregar", cada nombre tiene su "x" para eliminarlo).
- Interruptor **"Eliminar al ganador" / "Mantener a todos"**: decide si el
  nombre que sale sorteado se quita de la ruleta o puede volver a salir.
- Botón de idioma **ES / EN** arriba a la derecha, cambia toda la interfaz.
- Animación de la rueda con desaceleración realista (ease-out) y ligera
  rotación mientras está en reposo.
- Sonidos generados **por código** con `numpy` (clics al girar y una
  melodía de victoria) — no hay archivos de audio externos que empaquetar.
- Gráficos mejorados: fondo con degradado, luces de marquesina animadas
  alrededor de la mesa, sombra bajo la rueda, brillo metálico en el
  centro, texto con contorno para leerse bien sobre cualquier color, y
  confeti dorado al anunciar al ganador.

## 1. Ejecutar en tu PC

```bash
pip install -r requirements.txt
python main.py
```

## 2. Convertirlo en un .exe (Windows)

Todo el juego es un único archivo (`main.py`) y no usa assets externos
(las imágenes se dibujan con `pygame.draw` y los sonidos se generan con
`numpy`), así que empaquetarlo es muy directo.

1. Instala PyInstaller (idealmente **desde Windows**, no desde Linux/Mac,
   porque PyInstaller genera un ejecutable para el sistema operativo en el
   que se ejecuta):

   ```bash
   pip install pyinstaller
   ```

2. Genera el ejecutable de un solo archivo, sin consola:

   ```bash
   pyinstaller --onefile --noconsole --name RuletaCasino main.py
   ```

3. El resultado queda en `dist/RuletaCasino.exe`. Ese es el archivo que
   puedes compartir; no necesita Python instalado en la máquina destino.

### Notas útiles

- Si PyInstaller se queja de módulos de `numpy` no encontrados, prueba:
  ```bash
  pyinstaller --onefile --noconsole --name RuletaCasino ^
      --hidden-import=numpy.core._methods ^
      --hidden-import=numpy.lib.format main.py
  ```
- Si quieres un ícono propio, agrega `--icon=mi_icono.ico` al comando.
- Es normal que algunos antivirus marquen como sospechoso un `.exe` hecho
  con `--onefile` (falso positivo muy común en PyInstaller); si molesta,
  usa `--onedir` en vez de `--onefile` (genera una carpeta en lugar de un
  único archivo, pero suele dar menos falsos positivos).
- Prueba siempre el `.exe` generado en una máquina Windows limpia antes de
  distribuirlo.

## 3. Personalizar

- `names` — lista inicial de nombres de ejemplo (se pueden borrar/editar
  desde la app; no hace falta tocar el código).
- `MAX_NAMES` — límite de nombres que acepta la ruleta.
- `WHEEL_PALETTE` — colores que se van alternando en los sectores.
- `SPIN_DURATION` — duración del giro en milisegundos.
- `make_tone(...)` — ajusta frecuencia/duración/tipo de onda para cambiar
  cualquier efecto de sonido.
- `TEXTS` — diccionario con las traducciones ES/EN; agrega otro idioma
  duplicando el bloque y sumándolo al botón de idioma.
