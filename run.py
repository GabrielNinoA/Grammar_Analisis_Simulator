"""
Módulo: run.py
==============
Script lanzador principal del Analizador Sintáctico.

Propósito:
----------
Este script sirve como punto de entrada unificado para ejecutar la interfaz
gráfica del proyecto. Configura correctamente las rutas de Python y lanza
la GUI mejorada (enhanced_gui.py).

Ventajas de usar un launcher:
------------------------------
1. Configuración automática de rutas (sys.path)
2. Puede ejecutarse desde cualquier directorio
3. Manejo centralizado de errores de importación
4. Facilita la distribución del proyecto
5. Punto de entrada único y claro

Ejecución:
----------
    python run.py

Estructura del Proyecto Esperada:
----------------------------------
    Proyecto/
    ├── run.py          (este archivo)
    ├── src/            (módulos de lógica)
    │   ├── grammar.py
    │   ├── cnf.py
    │   ├── cyk_parser.py
    │   └── ...
    └── gui/            (interfaz gráfica)
        └── enhanced_gui.py
"""

import os
import sys
from PyQt6.QtWidgets import QApplication

# ============================================================================
# CONFIGURACIÓN DE RUTAS
# ============================================================================
# Determinar directorio base del proyecto (donde está este script)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Construir rutas absolutas a los directorios de módulos
SRC_DIR = os.path.join(BASE_DIR, "src")   # Módulos de lógica
GUI_DIR = os.path.join(BASE_DIR, "gui")   # Módulos de interfaz

# Agregar rutas al path de Python si no están presentes
# Esto permite importar módulos con "from src.X import Y" o "from gui.X import Y"
if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)
if GUI_DIR not in sys.path:
    sys.path.append(GUI_DIR)

# ============================================================================
# IMPORTACIÓN Y VERIFICACIÓN DE LA GUI
# ============================================================================
# Intentar importar la ventana principal de la GUI mejorada
try:
    from gui.enhanced_gui import MainWindow
except Exception as e:
    # Si falla la importación, mostrar mensaje detallado al usuario
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

# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================
def main():
    """
    Función principal que inicializa y ejecuta la aplicación GUI.
    
    Proceso:
    --------
    1. Crear instancia de QApplication (requerido por PyQt6)
    2. Crear ventana principal (MainWindow)
    3. Mostrar la ventana
    4. Entrar en el bucle de eventos de Qt
    5. Salir con el código de retorno apropiado
    
    Bucle de Eventos:
    -----------------
    app.exec() inicia el event loop de Qt, que:
    - Procesa eventos de usuario (clicks, teclado, etc.)
    - Redibuja la interfaz cuando es necesario
    - Mantiene la aplicación corriendo hasta que se cierre
    """
    print("🚀 Iniciando Analizador Sintáctico - GUI Mejorada...")
    
    # Crear aplicación Qt
    app = QApplication(sys.argv)
    
    # Crear y mostrar ventana principal
    window = MainWindow()
    window.show()
    
    # Iniciar bucle de eventos (bloquea hasta que se cierre la ventana)
    sys.exit(app.exec())

# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================
if __name__ == "__main__":
    main()
