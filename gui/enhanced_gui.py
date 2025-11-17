"""
Módulo: enhanced_gui.py
=======================
Interfaz Gráfica de Usuario (GUI) mejorada para el Analizador Sintáctico.

Framework: PyQt6
----------------
Utiliza PyQt6 para crear una interfaz moderna y funcional con múltiples pestañas.

Características Principales:
-----------------------------
1. **Editor de Gramáticas**: Crear y editar gramáticas interactivamente
2. **Parser CYK**: Probar cadenas y visualizar árboles de derivación
3. **Generador BFS**: Generar cadenas más cortas del lenguaje
4. **Persistencia**: Cargar y guardar gramáticas en JSON
5. **Visualización**: Árbol de parsing tanto textual como gráfico

Arquitectura:
-------------
- MainWindow: Ventana principal con pestañas
- TreeGraphicsView: Vista gráfica para árboles de derivación
- Integración con módulos src/: grammar, cyk_parser, generator, etc.

Estructura de Pestañas:
------------------------
1. **Editor de Gramática**
   - Campos para N, T, S
   - Lista de producciones
   - Botones para crear/cargar/guardar
   
2. **Parser & Árbol**
   - Campo de entrada para cadena
   - Visualización textual del árbol
   - Visualización gráfica del árbol
   
3. **Generador de Cadenas**
   - Selector de cantidad
   - Lista de cadenas generadas

Ejecución:
----------
    python -m gui.enhanced_gui
    
    O mejor aún, usar el launcher:
    python run.py
"""

from __future__ import annotations
import json
import os
import sys
from typing import Optional, Tuple, Any

from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QAction, QColor, QPainterPath, QFont
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QTextEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QFileDialog, QComboBox, QListWidget, QListWidgetItem,
    QMessageBox, QSplitter, QFrame, QTabWidget, QFormLayout, QGraphicsView, QGraphicsScene,
    QGraphicsEllipseItem, QGraphicsTextItem, QGraphicsLineItem, QSpinBox
)
from PyQt6.QtGui import QPainter


# ============================================================================
# IMPORTS DE MÓDULOS DE LÓGICA
# ============================================================================
# Estos módulos contienen toda la lógica de parsing, conversión CNF, etc.
# La GUI solo actúa como interfaz para estas funcionalidades

try:
    from src.grammar import Grammar           # Estructura de datos de gramáticas
    from src.storage import load_grammar, save_grammar  # Persistencia JSON
    from src.cyk_parser import cyk_parse, CYKResult    # Algoritmo CYK
    from src.generator import generate_shortest        # Generador BFS
    from src.tree_vis import render_tree_text          # Visualización textual
except Exception as e:
    # Si los imports fallan, dar mensaje útil
    msg = (
        "Error importando módulos desde 'src'. Asegúrate de ejecutar la GUI "
        "desde la raíz del proyecto con: python -m gui.enhanced_gui\n\n"
        f"Detalles: {e}"
    )
    raise ImportError(msg)


# ============================================================================
# FUNCIÓN AUXILIAR: Validación de Campos de Gramática
# ============================================================================
def validate_grammar_fields(N_text: str, T_text: str, productions_text: str, S_text: str) -> Tuple[bool, str]:
    """
    Valida que todos los campos necesarios para crear una gramática estén presentes.
    
    Retorna:
        (True, "") si todo es válido
        (False, mensaje_error) si falta algún campo
    """
    if not N_text.strip():
        return False, "Debe especificar al menos un No terminal (N)."
    if not T_text.strip():
        return False, "Debe especificar al menos un Terminal (T)."
    if not productions_text.strip():
        return False, "Debe agregar al menos una producción (P)."
    if not S_text.strip():
        return False, "Debe especificar el símbolo inicial (S)."
    return True, ""


# ============================================================================
# CLASE: TreeGraphicsView - Visualización Gráfica de Árboles
# ============================================================================
class TreeGraphicsView(QGraphicsView):
    """
    Widget personalizado para dibujar árboles de derivación de forma gráfica.
    
    Mejoras visuales:
    - Círculos con gradientes y sombras
    - Líneas curvas entre nodos
    - Colores diferentes para terminales y no terminales
    - Diseño balanceado automáticamente
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        # Configuración de rendering para calidad visual
        # Antialiasing: suaviza bordes de círculos y líneas
        self.setRenderHints(self.renderHints() | QPainter.RenderHint.Antialiasing)
        
        # Escena donde se dibujan los elementos gráficos
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        
        # =================================================================
        # PARÁMETROS DE DISEÑO DEL ÁRBOL (ajustados para mejor apariencia)
        # =================================================================
        self.node_radius = 30       # Radio de los círculos (aumentado)
        self.h_spacing = 80         # Espaciado horizontal entre hermanos (aumentado)
        self.v_spacing = 90         # Espaciado vertical entre niveles (aumentado)
        
        # Fuentes para símbolos (más grande y negrita)
        self.font_nt = QFont("Arial", 12, QFont.Weight.Bold)  # No terminales
        self.font_t = QFont("Arial", 11)                       # Terminales
        
        # Colores para diferentes tipos de nodos
        # No terminales: azul suave
        self.color_nt_bg = QColor(135, 206, 250)       # Fondo celeste
        self.color_nt_border = QColor(0, 100, 200)     # Borde azul oscuro
        
        # Terminales: verde suave
        self.color_t_bg = QColor(144, 238, 144)        # Fondo verde claro
        self.color_t_border = QColor(34, 139, 34)      # Borde verde oscuro
        
        # Color de líneas
        self.color_line = QColor(100, 100, 100)        # Gris medio

    def clear_scene(self):
        """Limpia todos los elementos gráficos de la escena."""
        self.scene.clear()

    def draw_tree(self, tree):
        """
        Dibuja el árbol de derivación completo en la escena gráfica.
        
        Parámetros:
        -----------
        tree : tuple
            Árbol en formato de tuplas anidadas retornado por CYK
            Formato: (símbolo, hijo1, hijo2, ...)
            Hoja terminal: (no_terminal, 'terminal')
            
        Algoritmo:
        ----------
        1. Normalizar el árbol a formato uniforme de tuplas
        2. Calcular anchos necesarios para cada subárbol (bottom-up)
        3. Dibujar recursivamente cada nodo con posición calculada
        4. Conectar nodos padre-hijo con líneas curvas
        5. Ajustar vista automáticamente al contenido
        """
        # Limpiar escena anterior
        self.scene.clear()
        
        # Si no hay árbol, no dibujar nada
        if not tree:
            return

        from PyQt6.QtGui import QPainter, QPen, QBrush, QRadialGradient
        import re

        # =================================================================
        # FUNCIÓN 1: Normalizar el árbol a formato estándar
        # =================================================================
        def normalize(node):
            """
            Convierte diferentes formatos de nodo a tupla estándar.
            - String solo: ('A',)
            - Tupla con hijos: ('A', hijo1, hijo2)
            """
            # Si es string, convertir a tupla de un elemento
            if isinstance(node, str):
                return (node,)
            
            # Si es lista o tupla, normalizar recursivamente
            if isinstance(node, (list, tuple)):
                # Normalizar cada hijo recursivamente
                normalized_children = [normalize(ch) for ch in node[1:]] if len(node) > 1 else []
                
                # Asegurar que el símbolo sea string
                head = node[0] if isinstance(node[0], str) else str(node[0])
                
                # Retornar tupla: (símbolo, hijo1, hijo2, ...)
                return tuple([head] + normalized_children)
            
            # Caso por defecto: convertir a string y envolver en tupla
            return (str(node),)

        # Normalizar árbol completo
        tree = normalize(tree)
        
        # =================================================================
        # FUNCIÓN 1.5: Simplificar árbol eliminando nodos T_X intermedios
        # =================================================================
        def simplify_tree(node):
            """
            Elimina nodos intermedios T_0, T_1, etc. creados por CNF.
            
            Estos nodos son artefactos de la conversión a Forma Normal de Chomsky
            donde cada terminal en una producción larga se reemplaza por T_X -> terminal.
            
            Ejemplo:
            Antes: ('A', ('T_0', 'a'), ('B', ...))
            Después: ('A', 'a', ('B', ...))
            
            Algoritmo:
            - Si el nodo es T_X con un solo hijo terminal, retornar el terminal
            - Si no, simplificar recursivamente cada hijo
            """
            # Extraer símbolo y lista de hijos
            if not isinstance(node, (tuple, list)):
                return node
            
            symbol = node[0] if len(node) > 0 else ""
            children = list(node[1:]) if len(node) > 1 else []
            
            # CASO ESPECIAL: Nodo T_X con un solo hijo que es terminal
            # Patrón: símbolo es T_0, T_1, T_2, etc. (generados por CNF)
            if re.match(r'^T_\d+$', str(symbol)) and len(children) == 1:
                # Verificar si el hijo es un terminal (string simple)
                child = children[0]
                
                # Si el hijo es una tupla de un elemento (terminal), devolver el string
                if isinstance(child, (tuple, list)) and len(child) == 1:
                    return child[0]
                
                # Si el hijo ya es string, devolverlo directamente
                if isinstance(child, str):
                    return child
                
                # Si tiene estructura (X, 'a'), devolver solo 'a'
                if isinstance(child, (tuple, list)) and len(child) == 2:
                    if isinstance(child[1], str):
                        return child[1]
            
            # CASO NORMAL: simplificar recursivamente cada hijo
            simplified_children = []
            for child in children:
                simplified = simplify_tree(child)
                simplified_children.append(simplified)
            
            # Retornar nodo con hijos simplificados
            return tuple([symbol] + simplified_children)
        
        # Simplificar el árbol para eliminar nodos T_X
        tree = simplify_tree(tree)

        # =================================================================
        # FUNCIÓN 2: Calcular ancho necesario para cada subárbol
        # =================================================================
        def compute_width(node):
            """
            Calcula el ancho horizontal necesario para dibujar un subárbol.
            Retorna: ancho en píxeles
            
            Algoritmo:
            - Nodo hoja: ancho = diámetro del círculo
            - Nodo interno: ancho = suma de anchos de hijos + espaciado
            """
            # Obtener símbolo y lista de hijos
            symbol = node[0] if isinstance(node, (tuple, list)) else str(node)
            children = node[1:] if isinstance(node, (tuple, list)) and len(node) > 1 else []
            
            # CASO 1: Nodo hoja (no tiene hijos)
            if not children:
                # Ancho mínimo = diámetro del círculo
                return 2 * self.node_radius
            
            # CASO 2: Nodo interno (tiene hijos)
            # Calcular recursivamente ancho de cada hijo
            child_widths = [compute_width(ch) for ch in children]
            
            # Ancho total = suma de anchos de hijos + espaciado entre ellos
            # Espaciado: (n-1) * h_spacing donde n = número de hijos
            total_width = sum(child_widths) + (len(children) - 1) * self.h_spacing
            
            # El ancho debe ser al menos el del nodo actual
            return max(total_width, 2 * self.node_radius)

        # =================================================================
        # FUNCIÓN 3: Determinar si un nodo es terminal
        # =================================================================
        def is_terminal(node):
            """
            Determina si un nodo representa un terminal.
            Formato de terminal: (no_terminal, 'terminal')
            Ejemplo: ('A', 'a')
            """
            # Verificar: exactamente 2 elementos Y segundo es string
            if isinstance(node, (tuple, list)) and len(node) == 2:
                # Segundo elemento debe ser string (el terminal)
                return isinstance(node[1], str)
            return False

        def display_symbol(node):
            """Retorna la etiqueta visible del nodo evitando mostrar T_i auxiliares."""
            symbol = node[0] if isinstance(node, (tuple, list)) else str(node)
            if is_terminal(node):
                terminal = node[1]
                if isinstance(symbol, str) and symbol.startswith("T_"):
                    return terminal
            return symbol

        # =================================================================
        # FUNCIÓN 4: Dibujar un nodo y sus hijos recursivamente
        # =================================================================
        def draw_node(node, x, y, width, depth=0):
            """
            Dibuja un nodo y recursivamente todos sus hijos.
            
            Parámetros:
            - node: tupla del nodo actual
            - x: posición x del centro del nodo
            - y: posición y del centro del nodo
            - width: ancho disponible para este subárbol
            - depth: profundidad en el árbol (0 = raíz)
            """
            # Radio del círculo
            r = self.node_radius
            
            # Extraer símbolo del nodo
            symbol = node[0] if isinstance(node, (tuple, list)) else str(node)
            visible_symbol = display_symbol(node)
            
            # Extraer lista de hijos
            children = node[1:] if isinstance(node, (tuple, list)) and len(node) > 1 else []
            
            # Determinar si es terminal para elegir colores
            is_term = is_terminal(node)
            
            # -------------------------------------------------------------
            # DIBUJAR CÍRCULO DEL NODO CON GRADIENTE
            # -------------------------------------------------------------
            # Crear círculo (elipse con ancho = alto)
            ellipse = QGraphicsEllipseItem(x - r, y - r, 2*r, 2*r)
            
            # Aplicar gradiente radial para efecto 3D
            gradient = QRadialGradient(x - r/3, y - r/3, r * 1.8)
            
            if is_term:
                # Terminal: gradiente verde
                gradient.setColorAt(0, QColor(200, 255, 200))  # Centro más claro
                gradient.setColorAt(1, self.color_t_bg)         # Borde color base
                ellipse.setPen(QPen(self.color_t_border, 2))   # Borde verde
            else:
                # No terminal: gradiente azul
                gradient.setColorAt(0, QColor(220, 240, 255))  # Centro más claro
                gradient.setColorAt(1, self.color_nt_bg)        # Borde color base
                ellipse.setPen(QPen(self.color_nt_border, 2))  # Borde azul
            
            # Aplicar el gradiente como brush (relleno)
            ellipse.setBrush(QBrush(gradient))
            
            # Agregar círculo a la escena
            self.scene.addItem(ellipse)
            
            # -------------------------------------------------------------
            # DIBUJAR TEXTO DEL SÍMBOLO CENTRADO
            # -------------------------------------------------------------
            text = QGraphicsTextItem(str(visible_symbol))
            
            # Aplicar fuente según tipo
            text.setFont(self.font_nt if not is_term else self.font_t)
            
            # Color del texto: negro
            text.setDefaultTextColor(QColor(0, 0, 0))
            
            # Centrar texto en el círculo
            # boundingRect(): rectángulo que contiene el texto
            text_rect = text.boundingRect()
            text.setPos(x - text_rect.width() / 2, y - text_rect.height() / 2)
            
            # Agregar texto a la escena
            self.scene.addItem(text)
            
            # -------------------------------------------------------------
            # SI NO HAY HIJOS, TERMINAR (nodo hoja)
            # -------------------------------------------------------------
            if not children:
                return
            
            # -------------------------------------------------------------
            # CALCULAR POSICIONES DE LOS HIJOS
            # -------------------------------------------------------------
            # Calcular ancho de cada hijo
            child_widths = [compute_width(ch) for ch in children]
            
            # Posición y de los hijos (un nivel más abajo)
            child_y = y + self.v_spacing
            
            # Calcular posición x inicial (lado izquierdo)
            total_children_width = sum(child_widths) + (len(children) - 1) * self.h_spacing
            current_x = x - total_children_width / 2
            
            # -------------------------------------------------------------
            # DIBUJAR CADA HIJO Y SU LÍNEA DE CONEXIÓN
            # -------------------------------------------------------------
            for i, ch in enumerate(children):
                # Ancho del hijo actual
                ch_width = child_widths[i]
                
                # Posición x del centro del hijo
                child_x = current_x + ch_width / 2
                
                # ---------------------------------------------------------
                # DIBUJAR LÍNEA CURVA DESDE PADRE A HIJO
                # ---------------------------------------------------------
                # Crear path para línea curva (Bézier)
                path = QPainterPath()
                
                # Punto inicial: borde inferior del círculo padre
                path.moveTo(x, y + r)
                
                # Punto de control para curva (punto medio vertical)
                control_y = (y + r + child_y - r) / 2
                
                # Curva cuadrática: desde padre hasta hijo
                # quadTo(control_x, control_y, end_x, end_y)
                path.quadTo(x, control_y, child_x, child_y - r)
                
                # Crear item gráfico desde el path
                line_item = self.scene.addPath(path, QPen(self.color_line, 2))
                
                # ---------------------------------------------------------
                # LLAMADA RECURSIVA: dibujar subárbol del hijo
                # ---------------------------------------------------------
                draw_node(ch, child_x, child_y, ch_width, depth + 1)
                
                # Avanzar posición x para el siguiente hijo
                # Sumar: ancho del hijo actual + espaciado
                current_x += ch_width + self.h_spacing

        # =================================================================
        # INICIAR DIBUJADO DESDE LA RAÍZ
        # =================================================================
        # Calcular ancho total necesario para el árbol
        total_width = compute_width(tree)
        
        # Dibujar desde la raíz en posición (0, 0)
        draw_node(tree, 0, 0, total_width)
        
        # =================================================================
        # AJUSTAR VISTA PARA MOSTRAR TODO EL ÁRBOL
        # =================================================================
        # Calcular rectángulo que contiene todos los elementos
        bounding = self.scene.itemsBoundingRect()
        
        # Agregar márgenes (10% en cada lado)
        margin = max(bounding.width(), bounding.height()) * 0.1
        bounding.adjust(-margin, -margin, margin, margin)
        
        # Establecer rectángulo de la escena
        self.setSceneRect(bounding)
        
        # Ajustar vista para mostrar todo (manteniendo aspect ratio)
        self.fitInView(bounding, Qt.AspectRatioMode.KeepAspectRatio)

# ============================================================================
# CLASE PRINCIPAL: MainWindow
# ============================================================================
class MainWindow(QMainWindow):
    """
    Ventana principal de la aplicación GUI.
    
    Gestiona las tres pestañas principales y coordina la interacción
    entre la interfaz y los módulos de lógica.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Analizador Sintáctico - GUI Mejorada")
        self.setMinimumSize(1000, 700)

        # Widget central: interfaz con pestañas
        tabs = QTabWidget()
        tabs.addTab(self.grammar_editor_tab(), "Editor de Gramática")
        tabs.addTab(self.parser_tab(), "Parser & Árbol")
        tabs.addTab(self.generator_tab(), "Generador de Cadenas")
        self.setCentralWidget(tabs)

        # Atributos de estado de la aplicación
        self.current_grammar: Optional[Grammar] = None  # Gramática actualmente cargada
        self.last_loaded_path: Optional[str] = None     # Última ruta de archivo usado

        # Crear menú
        self._create_menu()

    # ========================================================================
    # MENÚ SUPERIOR
    # ========================================================================
    def _create_menu(self):
        """Crea la barra de menú con opciones Archivo y Ayuda."""
        menubar = self.menuBar()
        
        # Menú Archivo
        file_menu = menubar.addMenu("&Archivo")

        load_act = QAction("Cargar Gramática", self)
        load_act.triggered.connect(self.menu_load)
        file_menu.addAction(load_act)

        save_act = QAction("Guardar Gramática", self)
        save_act.triggered.connect(self.menu_save)
        file_menu.addAction(save_act)

        exit_act = QAction("Salir", self)
        exit_act.triggered.connect(self.close)
        file_menu.addAction(exit_act)

        # Menú Ayuda
        help_menu = menubar.addMenu("&Ayuda")
        about_act = QAction("Acerca de", self)
        about_act.triggered.connect(lambda: QMessageBox.information(self, "Acerca de",
                                                                     "Analizador Sintáctico - GUI Mejorada\nProyecto Lenguajes Formales"))
        help_menu.addAction(about_act)

    # ========================================================================
    # PESTAÑA 1: EDITOR DE GRAMÁTICA
    # ========================================================================
    def grammar_editor_tab(self) -> QWidget:
        """
        Crea la pestaña del editor de gramáticas.
        
        Permite al usuario:
        - Ingresar N, T, S
        - Agregar producciones interactivamente
        - Crear gramática en memoria
        - Cargar/guardar desde archivos
        """
        w = QWidget()
        layout = QVBoxLayout()
        w.setLayout(layout)

        # Formulario para N, T, S
        form = QFormLayout()

        self.input_N = QLineEdit()
        self.input_N.setPlaceholderText("Ej: S,E,T,F,A,B (separados por comas)")
        form.addRow("No terminales (N):", self.input_N)

        self.input_T = QLineEdit()
        self.input_T.setPlaceholderText("Ej: a,b,0,1,+,* (separados por comas)")
        form.addRow("Terminales (T):", self.input_T)

        # Type selector
        self.combo_type = QComboBox()
        self.combo_type.addItems(["2 - Libre de Contexto (CFG)", "3 - Regular"])
        form.addRow("Tipo Gramática:", self.combo_type)

        self.input_S = QLineEdit()
        self.input_S.setPlaceholderText("Símbolo inicial, ej: S")
        form.addRow("Símbolo Inicial (S):", self.input_S)

        layout.addLayout(form)

        # Productions editor: two-column: left textarea to type production, right list of productions
        p_layout = QHBoxLayout()

        left_v = QVBoxLayout()
        self.production_editor = QLineEdit()
        self.production_editor.setPlaceholderText("Ej: S -> a S b | a")
        left_v.addWidget(QLabel("Escribir producción (formato A -> a B):"))
        left_v.addWidget(self.production_editor)
        btn_add = QPushButton("Agregar producción")
        btn_add.clicked.connect(self.add_production)
        left_v.addWidget(btn_add)

        p_layout.addLayout(left_v, 1)

        right_v = QVBoxLayout()
        right_v.addWidget(QLabel("Producciones (P):"))
        self.productions_list = QListWidget()
        right_v.addWidget(self.productions_list)
        row_btns = QHBoxLayout()
        btn_remove = QPushButton("Eliminar selección")
        btn_remove.clicked.connect(self.remove_selected_production)
        row_btns.addWidget(btn_remove)
        btn_clear = QPushButton("Limpiar producciones")
        btn_clear.clicked.connect(self.clear_productions)
        row_btns.addWidget(btn_clear)
        right_v.addLayout(row_btns)

        p_layout.addLayout(right_v, 2)

        layout.addLayout(p_layout)

        # Buttons: new/save/load/convert-to-json
        row2 = QHBoxLayout()
        btn_new = QPushButton("Crear Gramática desde campos")
        btn_new.clicked.connect(self.create_grammar_from_fields)
        row2.addWidget(btn_new)

        btn_load = QPushButton("Cargar Gramática (JSON)")
        btn_load.clicked.connect(self.menu_load)
        row2.addWidget(btn_load)

        btn_save = QPushButton("Guardar Gramática (JSON)")
        btn_save.clicked.connect(self.menu_save)
        row2.addWidget(btn_save)

        layout.addLayout(row2)

        # Status
        self.lab_status = QLabel("Estado: sin gramática")
        layout.addWidget(self.lab_status)

        return w

    def add_production(self):
        """Agrega producción(es) a la lista, soportando alternativas con |"""
        text = self.production_editor.text().strip()
        if not text:
            return
        # Soporta múltiples alternativas: S -> a | b se expande a dos producciones
        if '|' in text:
            left, rest = text.split('->') if '->' in text else text.split('→')
            left = left.strip()
            rhs_full = rest.strip()
            alternatives = [alt.strip() for alt in rhs_full.split('|')]
            for alt in alternatives:
                line = f"{left} -> {alt}"
                self.productions_list.addItem(line)
        else:
            self.productions_list.addItem(text)
        self.production_editor.clear()

    def remove_selected_production(self):
        """Elimina la producción seleccionada de la lista."""
        sel = self.productions_list.selectedItems()
        if not sel:
            return
        for item in sel:
            row = self.productions_list.row(item)
            self.productions_list.takeItem(row)

    def clear_productions(self):
        """Limpia toda la lista de producciones."""
        self.productions_list.clear()

    def create_grammar_from_fields(self):
        """
        Crea objeto Grammar desde los campos del formulario.
        
        Proceso:
        --------
        1. Recolectar datos de los campos de texto
        2. Validar que todos los campos necesarios estén presentes
        3. Parsear listas separadas por comas (N, T)
        4. Construir Grammar usando Grammar.from_text()
        5. Actualizar estado de la aplicación
        """
        N_text = self.input_N.text()
        T_text = self.input_T.text()
        productions = [self.productions_list.item(i).text() for i in range(self.productions_list.count())]
        S_text = self.input_S.text()
        
        # Validar campos
        ok, msg = validate_grammar_fields(N_text, T_text, "\n".join(productions), S_text)
        if not ok:
            QMessageBox.warning(self, "Validación", msg)
            return
        
        # Parsear listas
        N = [x.strip() for x in N_text.split(",") if x.strip()]
        T = [x.strip() for x in T_text.split(",") if x.strip()]
        gtype = '2' if self.combo_type.currentIndex() == 0 else '3'
        
        # Crear gramática
        try:
            g = Grammar.from_text(N, T, productions, S_text, gtype)
            self.current_grammar = g
            self.lab_status.setText(f"Estado: gramática creada. N={len(N)} T={len(T)} P={len(productions)}")
            QMessageBox.information(self, "OK", "Gramática creada y cargada en memoria.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo crear la gramática: {e}")

    # ========================================================================
    # PESTAÑA 2: PARSER CYK Y VISUALIZACIÓN DE ÁRBOL
    # ========================================================================
    def parser_tab(self) -> QWidget:
        """
        Crea la pestaña del parser.
        
        Componentes:
        - Campo de entrada para cadena
        - Vista textual del árbol de derivación
        - Vista gráfica del árbol de derivación
        """
        w = QWidget()
        layout = QVBoxLayout()
        w.setLayout(layout)

        top = QHBoxLayout()
        self.input_string = QLineEdit()
        self.input_string.setPlaceholderText("Ingrese la cadena (ej: abba) — no usar espacios si los terminales son caracteres simples")
        top.addWidget(QLabel("Cadena a probar:"))
        top.addWidget(self.input_string)
        btn_test = QPushButton("Probar cadena")
        btn_test.clicked.connect(self.run_parse)
        top.addWidget(btn_test)

        layout.addLayout(top)

        # Splitter: left textual tree + result, right graphical tree
        splitter = QSplitter(Qt.Orientation.Horizontal)

        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_widget.setLayout(left_layout)
        self.lab_result = QLabel("Resultado: —")
        left_layout.addWidget(self.lab_result)
        self.text_tree = QTextEdit()
        self.text_tree.setReadOnly(True)
        left_layout.addWidget(QLabel("Árbol (texto):"))
        left_layout.addWidget(self.text_tree)

        splitter.addWidget(left_widget)

        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_widget.setLayout(right_layout)
        right_layout.addWidget(QLabel("Árbol (gráfico):"))
        self.tree_view = TreeGraphicsView()
        right_layout.addWidget(self.tree_view)

        splitter.addWidget(right_widget)
        splitter.setSizes([420, 560])

        layout.addWidget(splitter)
        return w

    def run_parse(self):
        """
        Ejecuta el algoritmo CYK sobre la cadena ingresada.
        
        Proceso:
        --------
        1. Verificar que hay gramática cargada
        2. Obtener cadena de entrada
        3. Tokenizar apropiadamente (considerando terminales multi-carácter)
        4. Ejecutar CYK (que internamente convierte a CNF)
        5. Mostrar resultado: ACEPTADA/RECHAZADA
        6. Si es aceptada, visualizar árbol (textual y gráfico)
        
        Tokenización:
        -------------
        - Si terminales son de un carácter: split por caracteres
        - Si hay terminales multi-carácter: split por espacios
        """
        if not self.current_grammar:
            QMessageBox.warning(self, "Sin gramática", "Primero crea o carga una gramática.")
            return
        
        s = self.input_string.text().strip()
        
        # Determinar estrategia de tokenización basado en los terminales
        T = self.current_grammar.T
        multi = any(len(t) > 1 for t in T)
        
        if multi:
            # Terminales multi-carácter: usuario debe separar con espacios
            if s.strip() == "":
                tokens = []
            else:
                tokens = s.split()
        else:
            # Terminales simples: cada carácter es un token
            tokens = list(s)
        
        # Ejecutar algoritmo CYK
        try:
            res: CYKResult = cyk_parse(self.current_grammar, tokens)
        except Exception as e:
            QMessageBox.critical(self, "Error en parser", f"Excepción durante CYK: {e}")
            return
        
        # Mostrar resultado
        if res.accepted:
            self.lab_result.setText("Resultado: ACEPTADA ✅")
            if res.parse_tree:
                # Visualización textual
                self.text_tree.setPlainText(render_tree_text(res.parse_tree))
                # Visualización gráfica
                try:
                    self.tree_view.draw_tree(res.parse_tree)
                except Exception as e:
                    QMessageBox.warning(self, "Dibujo árbol", f"No se pudo dibujar el árbol: {e}")
        else:
            self.lab_result.setText("Resultado: RECHAZADA ❌")
            self.text_tree.clear()
            self.tree_view.clear_scene()

    # ========================================================================
    # PESTAÑA 3: GENERADOR DE CADENAS
    # ========================================================================
    def generator_tab(self) -> QWidget:
        """Crea la pestaña del generador BFS de cadenas."""
        w = QWidget()
        layout = QVBoxLayout()
        w.setLayout(layout)

        h = QHBoxLayout()
        h.addWidget(QLabel("Número de cadenas a generar:"))
        self.spin_limit = QSpinBox()
        self.spin_limit.setMinimum(1)
        self.spin_limit.setMaximum(100)
        self.spin_limit.setValue(10)
        h.addWidget(self.spin_limit)
        btn_gen = QPushButton("Generar (BFS)")
        btn_gen.clicked.connect(self.run_generate)
        h.addWidget(btn_gen)
        layout.addLayout(h)

        self.list_generated = QListWidget()
        layout.addWidget(self.list_generated)

        return w

    def run_generate(self):
        """
        Ejecuta el generador BFS para producir las N cadenas más cortas.
        
        Integración con generador:
        - Usa el módulo generator.generate_shortest()
        - Muestra resultados en lista numerada
        """
        if not self.current_grammar:
            QMessageBox.warning(self, "Sin gramática", "Primero crea o carga una gramática.")
            return
        
        limit = self.spin_limit.value()
        
        # Llamar al generador BFS
        try:
            gens = generate_shortest(self.current_grammar, limit=limit)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Excepción al generar: {e}")
            return
        
        # Mostrar resultados
        self.list_generated.clear()
        for i, s in enumerate(gens, 1):
            item = QListWidgetItem(f"{i}. {s!r}")
            self.list_generated.addItem(item)
        
        if not gens:
            QMessageBox.information(self, "Generador", "No se encontraron cadenas dentro de los límites definidos.")

    # ========================================================================
    # OPERACIONES DEL MENÚ: Cargar y Guardar
    # ========================================================================
    def menu_load(self):
        """
        Carga gramática desde archivo JSON.
        
        Integración con storage:
        - Usa load_grammar() del módulo storage
        - Actualiza todos los campos del editor con la gramática cargada
        - Maneja errores de archivo/formato
        """
        path, _ = QFileDialog.getOpenFileName(self, "Cargar Gramática (JSON)", "", "JSON Files (*.json);;All Files (*)")
        if not path:
            return
        
        try:
            g = load_grammar(path)
            self.current_grammar = g
            self.last_loaded_path = path
            
            # Rellenar campos del editor con la gramática cargada
            self.input_N.setText(", ".join(sorted(list(g.N))))
            self.input_T.setText(", ".join(sorted(list(g.T))))
            self.input_S.setText(g.S)
            
            # Rellenar lista de producciones
            self.productions_list.clear()
            for A, rhss in g.P.items():
                for rhs in rhss:
                    self.productions_list.addItem(f"{A} -> {' '.join(rhs)}")
            
            # Establecer tipo de gramática
            if g.gtype == '3':
                self.combo_type.setCurrentIndex(1)
            else:
                self.combo_type.setCurrentIndex(0)
            
            self.lab_status.setText(f"Estado: gramática cargada desde {os.path.basename(path)}")
            QMessageBox.information(self, "Cargado", f"Gramática cargada: {os.path.basename(path)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar la gramática: {e}")

    def menu_save(self):
        """
        Guarda gramática actual en archivo JSON.
        
        Integración con storage:
        - Usa save_grammar() del módulo storage
        - Sugiere última ruta usada como default
        - Maneja errores de escritura
        """
        if not self.current_grammar:
            # Si no hay gramática, intentar crearla desde los campos
            self.create_grammar_from_fields()
            if not self.current_grammar:
                return
        
        # Proponer ruta default
        if self.last_loaded_path:
            default = self.last_loaded_path
        else:
            default = os.path.join(os.getcwd(), "grammar.json")
        
        path, _ = QFileDialog.getSaveFileName(self, "Guardar Gramática (JSON)", default, "JSON Files (*.json);;All Files (*)")
        if not path:
            return
        
        try:
            save_grammar(self.current_grammar, path)
            self.last_loaded_path = path
            QMessageBox.information(self, "Guardado", f"Gramática guardada en:\n{path}")
            self.lab_status.setText(f"Estado: gramática guardada en {os.path.basename(path)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar: {e}")


# ============================================================================
# PUNTO DE ENTRADA DE LA GUI
# ============================================================================
def main():
    """Función principal que inicia la aplicación GUI."""
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
