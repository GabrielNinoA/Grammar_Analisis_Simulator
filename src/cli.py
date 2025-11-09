# contenido completo del módulo cli.py
import argparse
import sys
from .storage import save_grammar, load_grammar
from .grammar import Grammar
from .cyk_parser import cyk_parse
from .tree_vis import render_tree_text
from .generator import generate_shortest

def interactive_cli():
    print("Analizador Sintáctico - CLI")
    g: Grammar | None = None
    while True:
        print("\nOpciones:\n 1) Cargar gramática desde JSON\n 2) Mostrar gramática\n 3) Probar cadena\n 4) Generar 10 cadenas más cortas\n 5) Guardar gramática\n 6) Crear gramática manual\n 0) Salir")
        choice = input("Elige: ").strip()
        if choice == "1":
            path = input("Ruta al archivo JSON: ")
            try:
                g = load_grammar(path)
                print("Gramática cargada correctamente.")
            except Exception as e:
                print("Error al cargar:", e)
        elif choice == "2":
            if not g:
                print("No hay gramática cargada.")
            else:
                print(g)
        elif choice == "3":
            if not g:
                print("Carga una gramática primero.")
                continue
            s = input("Ingresa la cadena (sin espacios, terminales concatenados): ")
            w = list(s)
            res = cyk_parse(g, w)
            if res.accepted:
                print("Cadena ACEPTADA")
                if res.parse_tree:
                    print(render_tree_text(res.parse_tree))
            else:
                print("Cadena RECHAZADA")
        elif choice == "4":
            if not g:
                print("Carga una gramática primero.")
                continue
            print("Generando cadenas...")
            gens = generate_shortest(g, limit=10)
            for i, s in enumerate(gens, 1):
                print(f"{i}. '{s}'")
        elif choice == "5":
            if not g:
                print("No hay gramática para guardar.")
                continue
            path = input("Ruta destino (ej: grammar.json): ")
            save_grammar(g, path)
            print("Guardado.")
        elif choice == "6":
            print("Crear gramática manual")
            N = input("No terminales (separados por comas): ").split(",")
            N = [x.strip() for x in N if x.strip()]
            T = input("Terminales (separados por comas): ").split(",")
            T = [x.strip() for x in T if x.strip()]
            print("Introduce las producciones, línea por línea. Escribe una línea vacía para terminar.")
            P = []
            while True:
                line = input()
                if not line.strip():
                    break
                P.append(line.strip())
            S = input("Símbolo inicial: ")
            g = Grammar.from_text(N, T, P, S)
            print("Gramática creada.")
        elif choice == "0":
            print("Adiós")
            sys.exit(0)
        else:
            print("Opción no válida.")

if __name__ == '__main__':
    interactive_cli()
