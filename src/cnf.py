"""
Módulo: cnf.py - Conversión a Forma Normal de Chomsky (CNF)
============================================================
CNF requiere que todas las producciones sean:
  A -> BC (dos no terminales) o A -> a (un terminal)
"""

from __future__ import annotations
from typing import Dict, List, Tuple, Set
from .grammar import Grammar
import itertools


def to_cnf(grammar: Grammar) -> Grammar:
    """Convierte gramática a Forma Normal de Chomsky (CNF)"""
    
    # Copiar componentes de la gramática original (no modificar la original)
    N = set(grammar.N)  # Conjunto de no terminales {'S', 'A', 'B'}
    T = set(grammar.T)  # Conjunto de terminales {'a', 'b'}
    
    # Copiar producciones convirtiéndolas a tuplas inmutables
    # Ejemplo: {'S': [[('a',), ('b',)]]} → {'S': [('a',), ('b',)]}
    P = {A: [tuple(rhs) for rhs in rhss] for A, rhss in grammar.P.items()}
    
    # Guardar símbolo inicial
    S0 = grammar.S

    # =======================================================================
    # PASO 0: Proteger el símbolo inicial
    # =======================================================================
    # Si S aparece en lado derecho de producciones, crear nuevo S0 -> S
    # Esto evita que el símbolo inicial sea derivado por otras reglas
    
    new_start = S0  # Por defecto, mantener el mismo símbolo inicial
    
    # Verificar si S0 aparece en algún lado derecho
    # any(): retorna True si al menos una condición es verdadera
    # Recorre todas las producciones (rhss) de todos los no terminales
    # Luego recorre cada símbolo en cada producción (rhs)
    if any(S0 in rhs for rhss in P.values() for rhs in rhss):
        # S0 aparece en lado derecho, crear nuevo símbolo inicial
        new_start = S0 + "0"  # Ejemplo: 'S' → 'S0'
        N.add(new_start)  # Agregar nuevo símbolo a no terminales
        
        # Crear producción S0 -> S (el nuevo inicial deriva el antiguo)
        # setdefault: si new_start no existe en P, crea lista vacía
        P.setdefault(new_start, []).append((S0,))

    # =======================================================================
    # PASO 1: Eliminar producciones epsilon (ε-producciones)
    # =======================================================================
    
    # --- Paso 1a: Identificar símbolos "nullable" (que pueden derivar ε) ---
    
    nullable = set()  # Conjunto de símbolos que pueden generar cadena vacía
    changed = True  # Bandera para controlar el bucle de punto fijo
    
    # Algoritmo de punto fijo: repetir hasta que no haya cambios
    while changed:
        changed = False  # Asumir que no habrá cambios en esta iteración
        
        # Examinar cada no terminal A y sus producciones
        for A, rhss in P.items():
            for rhs in rhss:
                # Verificar si esta producción hace a A nullable
                # Condición 1: rhs vacío (len(rhs) == 0) → producción ε
                # Condición 2: todos los símbolos de rhs son nullable
                if len(rhs) == 0 or all((sym in nullable) for sym in rhs):
                    # Si A no estaba marcado como nullable, marcarlo ahora
                    if A not in nullable:
                        nullable.add(A)  # Agregar A al conjunto nullable
                        changed = True  # Hubo cambio, seguir iterando
    
    # --- Paso 1b: Expandir producciones eliminando nullable ---
    
    newP: Dict[str, List[Tuple[str, ...]]] = {}  # Nuevo conjunto de producciones
    
    # Procesar cada no terminal y sus producciones
    for A, rhss in P.items():
        new_rhs_set = set()  # Usar set para evitar duplicados
        
        # Procesar cada producción de A
        for rhs in rhss:
            # Identificar posiciones de símbolos nullable en esta producción
            # Ejemplo: rhs=('a', 'B', 'c') donde B es nullable → positions=[1]
            positions = [i for i, sym in enumerate(rhs) if sym in nullable]
            
            # Generar todas las combinaciones de eliminar/mantener nullable
            # Usamos máscara de bits: 2^n combinaciones (n = cantidad de nullable)
            # Ejemplo: si hay 2 nullable, mask va de 0 a 3 (00, 01, 10, 11 en binario)
            for mask in range(1 << len(positions)):  # 1 << n es igual a 2^n
                rhs_list = list(rhs)  # Convertir tupla a lista para modificar
                
                # Determinar qué símbolos eliminar según la máscara
                # Si bit i está en 1, eliminar el símbolo en positions[i]
                to_remove_indices = {positions[i] for i in range(len(positions)) 
                                    if (mask >> i) & 1}
                
                # Crear nueva producción sin los símbolos marcados
                # Ejemplo: ('a', 'B', 'c') sin índice 1 → ('a', 'c')
                new_rhs = tuple(sym for idx, sym in enumerate(rhs_list) 
                              if idx not in to_remove_indices)
                
                new_rhs_set.add(new_rhs)  # Agregar a set (evita duplicados)
        
        # Filtrar epsilon vacío excepto para el nuevo símbolo inicial
        # len(rhs) == 0: es producción vacía
        # A != new_start: no es el símbolo inicial
        final_rhs = [rhs for rhs in new_rhs_set 
                    if not (len(rhs) == 0 and A != new_start)]
        newP[A] = final_rhs
    
    # Reemplazar P con las nuevas producciones
    # Reemplazar P con las nuevas producciones
    P = newP

    # =======================================================================
    # PASO 2: Eliminar producciones unitarias (A -> B donde B es no terminal)
    # =======================================================================
    
    def remove_unit_productions(P: Dict[str, List[Tuple[str, ...]]]) -> Dict[str, List[Tuple[str, ...]]]:
        """Elimina todas las producciones unitarias calculando clausura transitiva"""
        
        # --- Paso 2a: Recolectar pares unitarios iniciales ---
        
        unit_pairs = set()  # Conjunto de pares (A, B) donde A -> B
        
        # Recorrer todas las producciones buscando unitarias
        for A in list(P.keys()):
            for rhs in P[A]:
                # Una producción es unitaria si:
                # 1. Tiene longitud 1: len(rhs) == 1
                # 2. Ese único símbolo es un no terminal: rhs[0] in N
                if len(rhs) == 1 and rhs[0] in N:
                    # Encontramos producción unitaria A -> B
                    unit_pairs.add((A, rhs[0]))  # Agregar par (A, B)
        
        # --- Paso 2b: Calcular clausura transitiva ---
        # Si A -> B y B -> C, entonces A -> C (transitividad)
        
        while True:  # Repetir hasta alcanzar punto fijo
            added = False  # Bandera para detectar si agregamos algo nuevo
            
            # Probar todas las combinaciones de pares existentes
            for (A, B) in list(unit_pairs):
                for (C, D) in list(unit_pairs):
                    # Si B = C (podemos encadenar A->B con B->D)
                    # y (A, D) no existe aún
                    if B == C and (A, D) not in unit_pairs:
                        unit_pairs.add((A, D))  # Agregar par transitivo
                        added = True  # Marcamos que hubo cambio
            
            # Si no se agregó nada nuevo, ya tenemos clausura completa
            if not added:
                break  # Salir del bucle
        
        # --- Paso 2c y 2d: Construir nuevas producciones sin unitarias ---
        
        # Crear diccionario con lista vacía para cada no terminal
        newP = {A: [] for A in N}
        
        # Para cada no terminal A
        for A in N:
            # Primero: agregar producciones no-unitarias de A
            for rhs in P.get(A, []):  # P.get(A, []) retorna [] si A no existe
                # Verificar si NO es unitaria
                if not (len(rhs) == 1 and rhs[0] in N):
                    newP[A].append(rhs)  # Agregar producción no-unitaria
            
            # Segundo: para cada B alcanzable desde A vía unitarias
            for (X, Y) in unit_pairs:
                if X == A:  # Si el par es (A, Y)
                    # Copiar producciones no-unitarias de Y a A
                    for rhs in P.get(Y, []):
                        # Solo copiar si NO es unitaria
                        if not (len(rhs) == 1 and rhs[0] in N):
                            # Verificar que no esté duplicada
                            if rhs not in newP[A]:
                                newP[A].append(rhs)
        
        return newP  # Retornar producciones sin unitarias
    
    # Llamar a la función para eliminar unitarias
    # Llamar a la función para eliminar unitarias
    P = remove_unit_productions(P)

    # =======================================================================
    # PASO 3: Reemplazar terminales en producciones largas
    # =======================================================================
    # En CNF, si una producción tiene 2+ símbolos, todos deben ser no terminales
    # Los terminales se reemplazan por nuevas variables: T_terminal -> terminal
    
    term_map: Dict[str, str] = {}  # Mapeo: terminal → variable creada
    counter = 0  # Contador para generar nombres únicos (T_0, T_1, ...)
    
    # Procesar cada no terminal y sus producciones
    for A in list(P.keys()):
        newlist = []  # Nueva lista de producciones para A
        
        for rhs in P[A]:
            # Solo procesar producciones con 2 o más símbolos
            if len(rhs) >= 2:
                new_rhs = list(rhs)  # Convertir tupla a lista para modificar
                
                # Examinar cada símbolo en la producción
                for i, sym in enumerate(rhs):
                    # Si el símbolo es terminal, debe reemplazarse
                    if sym in T:
                        # Verificar si ya creamos variable para este terminal
                        if sym in term_map:
                            # Ya existe, reutilizar la variable
                            var = term_map[sym]
                        else:
                            # Crear nueva variable para este terminal
                            var = f"T_{counter}"  # Ejemplo: T_0, T_1, T_2
                            counter += 1  # Incrementar contador
                            
                            # Verificar que el nombre no colisione con existentes
                            while var in N:
                                var = f"T_{counter}"
                                counter += 1
                            
                            # Agregar nueva variable a no terminales
                            N.add(var)
                            
                            # Crear producción T_i -> terminal
                            # setdefault: si var no existe en P, crear lista []
                            P.setdefault(var, []).append((sym,))
                            
                            # Guardar mapeo para reutilizar
                            term_map[sym] = var
                        
                        # Reemplazar terminal por variable en la producción
                        new_rhs[i] = var
                
                # Agregar producción modificada como tupla
                newlist.append(tuple(new_rhs))
            else:
                # Producción de longitud 1, mantenerla sin cambios
                # (puede ser A -> a o A -> B, ambas válidas en CNF)
                newlist.append(rhs)
        
        # Actualizar producciones de A
        P[A] = newlist

    # =======================================================================
    # PASO 4: Binarizar producciones largas (longitud > 2)
    # =======================================================================
    # Toda producción A -> B C D ... debe convertirse en binarias
    # Ejemplo: A -> B C D E se convierte en:
    #   A -> B X_0
    #   X_0 -> C X_1
    #   X_1 -> D E
    
    # Algoritmo iterativo: repetir hasta que no queden producciones largas
    while True:
        changed = False  # Bandera para detectar cambios
        
        # Examinar cada no terminal
        for A in list(P.keys()):
            new_rhss = []  # Nueva lista para producciones ya binarias
            
            for rhs in P[A]:
                # Verificar si la producción es larga (más de 2 símbolos)
                if len(rhs) > 2:
                    changed = True  # Encontramos producción larga
                    symbols = list(rhs)  # Convertir a lista
                    
                    # Crear cadena de variables intermedias
                    # Ejemplo: A -> B C D E
                    # Se convierte en: A -> B X_0, X_0 -> C X_1, X_1 -> D E
                    
                    cur_left = A  # Símbolo izquierdo actual
                    
                    # Iterar hasta el penúltimo par de símbolos
                    # range(len(symbols) - 2): si len=4, va de 0 a 1
                    for i in range(len(symbols) - 2):
                        first = symbols[i]  # Primer símbolo del par actual
                        
                        # Crear nombre único para variable intermedia
                        new_var = f"X_{len(N)}_{i}"
                        
                        # Asegurar unicidad (evitar colisiones de nombres)
                        while new_var in N:
                            new_var = f"X_{len(N)}_{i}_{i}"
                        
                        # Agregar nueva variable a no terminales
                        N.add(new_var)
                        
                        # Crear producción: cur_left -> first new_var
                        # Ejemplo: A -> B X_0
                        P.setdefault(cur_left, [])
                        P[cur_left].append((first, new_var))
                        
                        # Actualizar cur_left para siguiente iteración
                        cur_left = new_var  # Ahora cur_left es X_0, luego X_1, etc.
                    
                    # Crear última producción binaria con los 2 últimos símbolos
                    # Ejemplo: X_1 -> D E
                    last_two = (symbols[-2], symbols[-1])
                    P.setdefault(cur_left, [])
                    P[cur_left].append(last_two)
                else:
                    # Producción ya es binaria o unitaria, mantenerla
                    new_rhss.append(rhs)
            
            # Actualizar producciones de A (solo las binarias)
            P[A] = new_rhss
        
        # Si no hubo cambios, todas las producciones ya son binarias
        if not changed:
            break  # Terminar el bucle

    # =======================================================================
    # LIMPIEZA FINAL: Eliminar producciones duplicadas
    # =======================================================================
    for A in list(P.keys()):
        seen = []  # Lista de producciones ya vistas
        for rhs in P[A]:
            # Solo agregar si no está duplicada
            if rhs not in seen:
                seen.append(rhs)
        P[A] = seen  # Actualizar con lista sin duplicados

    # Crear y retornar nueva gramática en CNF
    return Grammar(N, T, P, new_start, grammar.gtype)
