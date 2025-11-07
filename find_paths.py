# find_paths.py (CORREGIDO)
import ttkthemes
import tkcalendar
from pathlib import Path

# Método robusto para encontrar la carpeta de temas
themes_path = Path(ttkthemes.__file__).parent / 'themes'
tkcalendar_path = Path(tkcalendar.__file__).parent

print(f"Ruta de ttkthemes: {themes_path}")
print(f"Ruta de tkcalendar: {tkcalendar_path}")