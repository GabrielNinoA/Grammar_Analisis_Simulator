"""
Lanzador principal del Analizador Sintáctico (Proyecto Formales)
---------------------------------------------------------------
Este script ejecuta directamente la interfaz gráfica mejorada
(gui/enhanced_gui.py), garantizando que las rutas estén configuradas
correctamente incluso si se ejecuta desde cualquier ubicación.

Ejecución:
    python run.py
"""

import os
import sys
from PyQt6.QtWidgets import QApplication

# -------------------------------------------------------------------
# CONFIGURACIÓN DE RUTAS
# -------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")
GUI_DIR = os.path.join(BASE_DIR, "gui")

# Agregamos las rutas necesarias al path de Python
if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)
if GUI_DIR not in sys.path:
    sys.path.append(GUI_DIR)

# -------------------------------------------------------------------
# IMPORTAMOS LA GUI MEJORADA
# -------------------------------------------------------------------
try:
    from gui.enhanced_gui import MainWindow
except Exception as e:
    print("❌ No se pudo importar la GUI mejorada (gui/enhanced_gui.py)")
    print("Asegúrate de tener la estructura correcta del proyecto:")
    print("""
Proyecto_Analizador_Completo/
├── run.py
├── src/
│   ├── grammar.py
│   ├── storage.py
│   ├── cyk_parser.py
│   ├── generator.py
│   ├── tree_vis.py
│   └── ...
└── gui/
    └── enhanced_gui.py
    """)
    print(f"Detalles del error: {e}")
    sys.exit(1)

# -------------------------------------------------------------------
# FUNCIÓN PRINCIPAL
# -------------------------------------------------------------------
def main():
    print("🚀 Iniciando Analizador Sintáctico - GUI Mejorada...")
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

# -------------------------------------------------------------------
# PUNTO DE ENTRADA
# -------------------------------------------------------------------
if __name__ == "__main__":
    main()
