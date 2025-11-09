# Analizador Sintáctico (Tipo 2 y Tipo 3) - Proyecto

Este repositorio implementa un analizador sintáctico (parser) y generador de cadenas para
Gramáticas Libres de Contexto (Tipo 2) y Gramáticas Regulares (Tipo 3).

**Características principales**:
- Definir gramáticas como tupla G = (N, T, P, S).
- Guardar / cargar gramáticas en JSON.
- Parser para CFG usando el algoritmo CYK (se convierte la gramática a CNF).
- Reconstrucción y visualización textual del árbol de derivación.
- Generador de las 10 primeras cadenas más cortas usando BFS en el espacio de derivaciones.
- CLI (consola) y una GUI simple en PyQt6 (opcional).

## Requisitos
- Python 3.10+
- `pip install -r requirements.txt` (si usas la GUI instala PyQt6)

## Uso (CLI)
Desde la raíz del proyecto:
Sigue las instrucciones para:
- Crear/editar una gramática.
- Guardar / cargar gramáticas (JSON).
- Probar cadenas (Aceptar/Rechazar) y ver árbol de derivación.
- Generar las 10 cadenas más cortas.

## Notas
- El parser CFG utiliza CYK y requiere convertir la gramática a Forma Normal de Chomsky (CNF).
- Para gramáticas regulares (Tipo 3) puedes usar los mismos módulos; la conversión a CNF es directa en la mayoría de casos.
