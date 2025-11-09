"""
GUI mejorada del Analizador Sintáctico (PyQt6)

Ejecutar desde la raíz del proyecto con:
    python -m gui.enhanced_gui

La GUI importa los módulos del paquete `src`:
    from src.grammar import Grammar
    from src.storage import load_grammar, save_grammar
    from src.cyk_parser import cyk_parse
    from src.generator import generate_shortest
    from src.tree_vis import render_tree_text
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



# IMPORTS from src package (requires running as module from project root)
try:
    from src.grammar import Grammar
    from src.storage import load_grammar, save_grammar
    from src.cyk_parser import cyk_parse, CYKResult
    from src.generator import generate_shortest
    from src.tree_vis import render_tree_text
except Exception as e:
    # If imports fail, give a helpful message
    msg = (
        "Error importando módulos desde 'src'. Asegúrate de ejecutar la GUI "
        "desde la raíz del proyecto con: python -m gui.enhanced_gui\n\n"
        f"Detalles: {e}"
    )
    raise ImportError(msg)


# -------------------------
# Helper: validate grammar fields
# -------------------------
def validate_grammar_fields(N_text: str, T_text: str, productions_text: str, S_text: str) -> Tuple[bool, str]:
    if not N_text.strip():
        return False, "Debe especificar al menos un No terminal (N)."
    if not T_text.strip():
        return False, "Debe especificar al menos un Terminal (T)."
    if not productions_text.strip():
        return False, "Debe agregar al menos una producción (P)."
    if not S_text.strip():
        return False, "Debe especificar el símbolo inicial (S)."
    return True, ""


# -------------------------
# Graphics: draw parse tree in QGraphicsScene
# -------------------------
class TreeGraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHints(self.renderHints() | QPainter.RenderHint.Antialiasing)
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.node_radius = 28
        self.h_spacing = 18
        self.v_spacing = 60
        self.font = QFont("Arial", 10)

    def clear_scene(self):
        self.scene.clear()

    def draw_tree(self, tree):
        """Dibuja el árbol de derivación de forma segura y sin errores."""
        self.scene.clear()
        if not tree:
            return

        from PyQt6.QtGui import QPainter

        # Normaliza el árbol: convierte cualquier str o lista a tupla uniforme
        def normalize(node):
            if isinstance(node, str):
                return (node,)
            if isinstance(node, (list, tuple)):
                normalized_children = [normalize(ch) for ch in node[1:]] if len(node) > 1 else []
                head = node[0] if isinstance(node[0], str) else str(node[0])
                return tuple([head] + normalized_children)
            return (str(node),)

        tree = normalize(tree)

        # Dibuja el árbol recursivamente
        def draw_node(node, x, y, depth=0):
            r = self.node_radius
            symbol = node[0] if isinstance(node, (tuple, list)) else str(node)
            children = node[1:] if isinstance(node, (tuple, list)) and len(node) > 1 else []

            # Dibujar nodo actual
            ellipse = QGraphicsEllipseItem(x - r, y - r, 2*r, 2*r)
            ellipse.setBrush(QColor(230, 240, 255))
            ellipse.setPen(QColor(0, 0, 80))
            self.scene.addItem(ellipse)

            text = QGraphicsTextItem(str(symbol))
            text.setFont(self.font)
            text.setDefaultTextColor(QColor(10, 10, 10))
            text.setPos(x - text.boundingRect().width() / 2, y - text.boundingRect().height() / 2)
            self.scene.addItem(text)

            if not children:
                return

            # Distribuye los hijos horizontalmente
            total_width = len(children) * (self.node_radius * 3)
            start_x = x - total_width / 2
            child_y = y + self.v_spacing

            for i, ch in enumerate(children):
                child_x = start_x + i * (self.node_radius * 3)
                line = QGraphicsLineItem(x, y + r, child_x, child_y - r)
                self.scene.addItem(line)
                draw_node(ch, child_x, child_y, depth + 1)

        # Dibujar desde el nodo raíz
        draw_node(tree, 0, 0)

        # Ajustar vista automáticamente
        self.setSceneRect(self.scene.itemsBoundingRect())
        self.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

# -------------------------
# Main Window
# -------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Analizador Sintáctico - GUI Mejorada")
        self.setMinimumSize(1000, 700)

        # Central widget: Tabbed interface
        tabs = QTabWidget()
        tabs.addTab(self.grammar_editor_tab(), "Editor de Gramática")
        tabs.addTab(self.parser_tab(), "Parser & Árbol")
        tabs.addTab(self.generator_tab(), "Generador de Cadenas")
        self.setCentralWidget(tabs)

        # Attributes
        self.current_grammar: Optional[Grammar] = None
        self.last_loaded_path: Optional[str] = None

        # Menu
        self._create_menu()

    # -------------------------
    # Menu bar
    # -------------------------
    def _create_menu(self):
        menubar = self.menuBar()
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

        help_menu = menubar.addMenu("&Ayuda")
        about_act = QAction("Acerca de", self)
        about_act.triggered.connect(lambda: QMessageBox.information(self, "Acerca de",
                                                                     "Analizador Sintáctico - GUI Mejorada\nProyecto Lenguajes Formales"))
        help_menu.addAction(about_act)

    # -------------------------
    # Tab: Grammar Editor
    # -------------------------
    def grammar_editor_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout()
        w.setLayout(layout)

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
        text = self.production_editor.text().strip()
        if not text:
            return
        # Allow multiple alternatives separated by '|'
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
        sel = self.productions_list.selectedItems()
        if not sel:
            return
        for item in sel:
            row = self.productions_list.row(item)
            self.productions_list.takeItem(row)

    def clear_productions(self):
        self.productions_list.clear()

    def create_grammar_from_fields(self):
        N_text = self.input_N.text()
        T_text = self.input_T.text()
        productions = [self.productions_list.item(i).text() for i in range(self.productions_list.count())]
        S_text = self.input_S.text()
        ok, msg = validate_grammar_fields(N_text, T_text, "\n".join(productions), S_text)
        if not ok:
            QMessageBox.warning(self, "Validación", msg)
            return
        N = [x.strip() for x in N_text.split(",") if x.strip()]
        T = [x.strip() for x in T_text.split(",") if x.strip()]
        gtype = '2' if self.combo_type.currentIndex() == 0 else '3'
        try:
            g = Grammar.from_text(N, T, productions, S_text, gtype)
            self.current_grammar = g
            self.lab_status.setText(f"Estado: gramática creada. N={len(N)} T={len(T)} P={len(productions)}")
            QMessageBox.information(self, "OK", "Gramática creada y cargada en memoria.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo crear la gramática: {e}")

    # -------------------------
    # Tab: Parser & Tree
    # -------------------------
    def parser_tab(self) -> QWidget:
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
        if not self.current_grammar:
            QMessageBox.warning(self, "Sin gramática", "Primero crea o carga una gramática.")
            return
        s = self.input_string.text().strip()
        # For safety: if grammar terminals are multi-character tokens, the UI expects chars; user can input tokens separated by spaces.
        # Try: if terminals contain any multi-char element, split on spaces, else split into chars.
        T = self.current_grammar.T
        multi = any(len(t) > 1 for t in T)
        if multi:
            if s.strip() == "":
                tokens = []
            else:
                tokens = s.split()
        else:
            tokens = list(s)
        # Run CYK
        try:
            res: CYKResult = cyk_parse(self.current_grammar, tokens)
        except Exception as e:
            QMessageBox.critical(self, "Error en parser", f"Excepción durante CYK: {e}")
            return
        if res.accepted:
            self.lab_result.setText("Resultado: ACEPTADA ✅")
            if res.parse_tree:
                self.text_tree.setPlainText(render_tree_text(res.parse_tree))
                # draw graphical tree
                try:
                    self.tree_view.draw_tree(res.parse_tree)
                except Exception as e:
                    QMessageBox.warning(self, "Dibujo árbol", f"No se pudo dibujar el árbol: {e}")
        else:
            self.lab_result.setText("Resultado: RECHAZADA ❌")
            self.text_tree.clear()
            self.tree_view.clear_scene()

    # -------------------------
    # Tab: Generator
    # -------------------------
    def generator_tab(self) -> QWidget:
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
        if not self.current_grammar:
            QMessageBox.warning(self, "Sin gramática", "Primero crea o carga una gramática.")
            return
        limit = self.spin_limit.value()
        try:
            gens = generate_shortest(self.current_grammar, limit=limit)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Excepción al generar: {e}")
            return
        self.list_generated.clear()
        for i, s in enumerate(gens, 1):
            item = QListWidgetItem(f"{i}. {s!r}")
            self.list_generated.addItem(item)
        if not gens:
            QMessageBox.information(self, "Generador", "No se encontraron cadenas dentro de los límites definidos.")

    # -------------------------
    # Menu actions: load / save
    # -------------------------
    def menu_load(self):
        path, _ = QFileDialog.getOpenFileName(self, "Cargar Gramática (JSON)", "", "JSON Files (*.json);;All Files (*)")
        if not path:
            return
        try:
            g = load_grammar(path)
            self.current_grammar = g
            self.last_loaded_path = path
            # fill fields
            self.input_N.setText(", ".join(sorted(list(g.N))))
            self.input_T.setText(", ".join(sorted(list(g.T))))
            self.input_S.setText(g.S)
            # productions list
            self.productions_list.clear()
            for A, rhss in g.P.items():
                for rhs in rhss:
                    self.productions_list.addItem(f"{A} -> {' '.join(rhs)}")
            # type
            if g.gtype == '3':
                self.combo_type.setCurrentIndex(1)
            else:
                self.combo_type.setCurrentIndex(0)
            self.lab_status.setText(f"Estado: gramática cargada desde {os.path.basename(path)}")
            QMessageBox.information(self, "Cargado", f"Gramática cargada: {os.path.basename(path)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar la gramática: {e}")

    def menu_save(self):
        if not self.current_grammar:
            # try to build from fields
            self.create_grammar_from_fields()
            if not self.current_grammar:
                return
        # propose last_loaded_path or ask for new
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


# -------------------------
# Entrypoint
# -------------------------
def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
