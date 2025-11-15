"""
Módulo: cli.py - Interfaz de línea de comandos interactiva
===========================================================
Menú interactivo para cargar, visualizar, parsear y generar gramáticas.
"""

import argparse
import sys
from .storage import save_grammar, load_grammar
from .grammar import Grammar
from .cyk_parser import cyk_parse
from .tree_vis import render_tree_text
from .generator import generate_shortest


def interactive_cli():
    """
    Bucle interactivo con menú de 7 opciones para manipular gramáticas.
    """
    
    # Mostrar título del programa
    print("Analizador Sintáctico - CLI")
    
    # Variable de estado: gramática actual cargada
    # None si no hay gramática cargada
    g: Grammar | None = None
    
    # =======================================================================
    # BUCLE PRINCIPAL: repetir hasta que usuario elija salir (opción 0)
    # =======================================================================
    while True:
        # ===================================================================
        # MOSTRAR MENÚ
        # ===================================================================
        print("\nOpciones:")
        print(" 1) Cargar gramática desde JSON")
        print(" 2) Mostrar gramática")
        print(" 3) Probar cadena")
        print(" 4) Generar 10 cadenas más cortas")
        print(" 5) Guardar gramática")
        print(" 6) Crear gramática manual")
        print(" 0) Salir")
        
        # Leer entrada del usuario y eliminar espacios en blanco
        # strip(): quita espacios al inicio y final
        choice = input("Elige: ").strip()
        
        # ===================================================================
        # OPCIÓN 1: Cargar gramática desde archivo JSON
        # ===================================================================
        if choice == "1":
            # Solicitar ruta al usuario
            path = input("Ruta al archivo JSON: ")
            
            try:
                # Intentar cargar gramática desde el archivo
                # load_grammar(): lee JSON y construye Grammar
                g = load_grammar(path)
                print("Gramática cargada correctamente.")
            
            except Exception as e:
                # Capturar cualquier error (archivo no existe, JSON inválido, etc.)
                # Mostrar mensaje de error sin terminar el programa
                print("Error al cargar:", e)
        
        # ===================================================================
        # OPCIÓN 2: Mostrar gramática actual
        # ===================================================================
        elif choice == "2":
            # Verificar si hay gramática cargada
            if not g:
                print("No hay gramática cargada.")
            else:
                # Imprimir gramática (usa método __str__ de Grammar)
                # Muestra N, T, S y todas las producciones
                print(g)
        
        # ===================================================================
        # OPCIÓN 3: Probar cadena con parser CYK
        # ===================================================================
        elif choice == "3":
            # Verificar que haya gramática cargada
            if not g:
                print("Carga una gramática primero.")
                continue  # Volver al inicio del bucle (mostrar menú de nuevo)
            
            # Solicitar cadena al usuario
            s = input("Ingresa la cadena (sin espacios, terminales concatenados): ")
            
            # Convertir string a lista de símbolos
            # Ejemplo: "aaabbb" → ['a', 'a', 'a', 'b', 'b', 'b']
            w = list(s)
            
            # Ejecutar algoritmo CYK
            # cyk_parse(): retorna CYKResult con accepted y parse_tree
            res = cyk_parse(g, w)
            
            # Verificar si la cadena fue aceptada
            if res.accepted:
                print("Cadena ACEPTADA")
                
                # Si hay árbol de derivación, mostrarlo
                if res.parse_tree:
                    # render_tree_text(): convierte árbol tupla a texto indentado
                    print(render_tree_text(res.parse_tree))
            else:
                print("Cadena RECHAZADA")
        
        # ===================================================================
        # OPCIÓN 4: Generar cadenas más cortas
        # ===================================================================
        elif choice == "4":
            # Verificar que haya gramática cargada
            if not g:
                print("Carga una gramática primero.")
                continue  # Volver al menú
            
            print("Generando cadenas...")
            
            # Generar hasta 10 cadenas más cortas
            # generate_shortest(): usa BFS para generar cadenas en orden de longitud
            gens = generate_shortest(g, limit=10)
            
            # Mostrar cadenas generadas con numeración
            # enumerate(gens, 1): empezar numeración en 1 (no en 0)
            for i, s in enumerate(gens, 1):
                # f-string: formatear salida como "1. 'cadena'"
                print(f"{i}. '{s}'")
        
        # ===================================================================
        # OPCIÓN 5: Guardar gramática en JSON
        # ===================================================================
        elif choice == "5":
            # Verificar que haya gramática para guardar
            if not g:
                print("No hay gramática para guardar.")
                continue  # Volver al menú
            
            # Solicitar ruta de destino
            path = input("Ruta destino (ej: grammar.json): ")
            
            # Guardar gramática en formato JSON
            # save_grammar(): serializa g a JSON con indentación
            save_grammar(g, path)
            print("Guardado.")
        
        # ===================================================================
        # OPCIÓN 6: Crear gramática manualmente
        # ===================================================================
        elif choice == "6":
            print("Crear gramática manual")
            
            # -----------------------------------------------------------
            # Paso 1: Solicitar no terminales
            # -----------------------------------------------------------
            # input(): obtener string del usuario
            # split(","): dividir por comas → lista
            N = input("No terminales (separados por comas): ").split(",")
            
            # Limpiar espacios y filtrar vacíos
            # x.strip(): quitar espacios de cada elemento
            # if x.strip(): solo incluir si no está vacío
            N = [x.strip() for x in N if x.strip()]
            
            # -----------------------------------------------------------
            # Paso 2: Solicitar terminales
            # -----------------------------------------------------------
            T = input("Terminales (separados por comas): ").split(",")
            # Limpiar espacios y filtrar vacíos
            T = [x.strip() for x in T if x.strip()]
            
            # -----------------------------------------------------------
            # Paso 3: Solicitar producciones línea por línea
            # -----------------------------------------------------------
            print("Introduce las producciones, línea por línea. Escribe una línea vacía para terminar.")
            
            # Lista para almacenar producciones
            P = []
            
            # Bucle: leer líneas hasta que usuario ingrese línea vacía
            while True:
                line = input()
                
                # Si línea está vacía (solo espacios), terminar bucle
                if not line.strip():
                    break
                
                # Agregar línea (sin espacios extra) a lista de producciones
                P.append(line.strip())
            
            # -----------------------------------------------------------
            # Paso 4: Solicitar símbolo inicial
            # -----------------------------------------------------------
            S = input("Símbolo inicial: ")
            
            # -----------------------------------------------------------
            # Paso 5: Construir gramática
            # -----------------------------------------------------------
            # Grammar.from_text(): método estático que parsea texto a Grammar
            # Recibe: listas N, T, P y string S
            g = Grammar.from_text(N, T, P, S)
            print("Gramática creada.")
        
        # ===================================================================
        # OPCIÓN 0: Salir del programa
        # ===================================================================
        elif choice == "0":
            print("Adiós")
            # sys.exit(0): terminar programa con código de éxito (0)
            sys.exit(0)
        
        # ===================================================================
        # OPCIÓN INVÁLIDA
        # ===================================================================
        else:
            print("Opción no válida.")


# Punto de entrada si se ejecuta el módulo directamente
# __name__ == '__main__': True cuando se ejecuta "python cli.py"
if __name__ == '__main__':
    interactive_cli()
