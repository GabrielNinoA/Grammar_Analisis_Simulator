# contenido completo del módulo simple_gui.py
# GUI mínima en PyQt6. Ejecutar solo si PyQt6 está instalado.

from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QTextEdit, QPushButton, QFileDialog, QLabel, QLineEdit)
import sys
from src.storage import load_grammar, save_grammar
from src.cyk_parser import cyk_parse
from src.generator import generate_shortest
from src.tree_vis import render_tree_text

class SimpleApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Analizador Sintáctico - GUI Simple')
        self.setMinimumSize(800, 600)
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.info = QLabel('Carga una gramática JSON o crea una desde la CLI')
        layout.addWidget(self.info)

        btn_load = QPushButton('Cargar Gramática')
        btn_load.clicked.connect(self.load)
        layout.addWidget(btn_load)

        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText('Ingresa cadena a probar')
        layout.addWidget(self.input_line)

        btn_test = QPushButton('Probar cadena')
        btn_test.clicked.connect(self.test)
        layout.addWidget(btn_test)

        self.out = QTextEdit()
        layout.addWidget(self.out)

        btn_gen = QPushButton('Generar 10 cadenas')
        btn_gen.clicked.connect(self.gen)
        layout.addWidget(btn_gen)

        self.grammar = None

    def load(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Abrir gramática', '', 'JSON Files (*.json)')
        if path:
            try:
                self.grammar = load_grammar(path)
                self.out.append('Gramática cargada: ' + path)
            except Exception as e:
                self.out.append('Error: ' + str(e))

    def test(self):
        if not self.grammar:
            self.out.append('Carga una gramática primero')
            return
        s = self.input_line.text().strip()
        res = cyk_parse(self.grammar, list(s))
        if res.accepted:
            self.out.append('Cadena ACEPTADA')
            if res.parse_tree:
                self.out.append(render_tree_text(res.parse_tree))
        else:
            self.out.append('Cadena RECHAZADA')

    def gen(self):
        if not self.grammar:
            self.out.append('Carga una gramática primero')
            return
        gens = generate_shortest(self.grammar, 10)
        self.out.append('Generadas:')
        for s in gens:
            self.out.append(s)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = SimpleApp()
    w.show()
    sys.exit(app.exec())
