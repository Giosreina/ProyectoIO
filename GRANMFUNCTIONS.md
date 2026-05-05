## Arquitectura de Software

El proyecto implementa una aplicación de escritorio para resolver problemas de programación lineal utilizando el Método de la Gran M. La arquitectura sigue un patrón Modelo-Vista-Controlador (MVC) simplificado:

- **Modelo**: Las funciones `parse_expr`, `parse_constraint`, `solve_gran_m` y `fmt_frac` manejan la lógica de negocio, incluyendo el parsing de expresiones, la resolución del problema y el formateo de resultados.
- **Vista**: La interfaz gráfica de usuario (GUI) está construida con PyQt6, utilizando widgets como `QMainWindow`, `QWidget`, `QTableWidget`, etc., para mostrar entradas, resultados y iteraciones del algoritmo.
- **Controlador**: La clase `InputPanel` y otras clases de la GUI manejan la interacción del usuario, recopilando entradas y disparando la resolución del problema.

El flujo de ejecución comienza en la GUI, donde el usuario ingresa datos, luego se invoca `solve_gran_m` para calcular la solución, y finalmente se muestran los resultados en tablas y texto formateado.

## Librerías Utilizadas

- **sys**: Para manejo del sistema y argumentos de línea de comandos.
- **re**: Para expresiones regulares, utilizado en el parsing de expresiones matemáticas.
- **fractions.Fraction**: Para representar coeficientes y valores con precisión fraccionaria, evitando errores de punto flotante.
- **PyQt6.QtWidgets**: Para crear la interfaz gráfica, incluyendo ventanas, botones, tablas y layouts.
- **PyQt6.QtCore**: Para señales, hilos y utilidades básicas de Qt, como `QThread` y `QTimer`.
- **PyQt6.QtGui**: Para elementos gráficos como fuentes, colores y gradientes utilizados en el estilo de la aplicación.

## Función: `parse_expr(expr_str, var_names)`

**Descripción**: Parsea una expresión lineal en forma de cadena y extrae los coeficientes de las variables especificadas.

**Parámetros**:
- `expr_str` (str): La expresión a parsear, ej. "5x1 + 4x2 + 3x3".
- `var_names` (list): Lista de nombres de variables, ej. ["x1", "x2", "x3"].

**Retorno**: Un diccionario donde las claves son los nombres de variables y los valores son los coeficientes como objetos `Fraction`.

**Lógica**:
- Reemplaza espacios y convierte restas a sumas negativas.
- Divide la expresión en términos separados por "+".
- Para cada término, usa expresiones regulares para identificar coeficientes y variables.
- Maneja casos especiales como coeficientes implícitos (1 o -1).

**Ejemplo**:
```python
parse_expr("5x1 + 4x2", ["x1", "x2"])  # {"x1": Fraction(5,1), "x2": Fraction(4,1)}
```

## Función: `parse_constraint(line, var_names)`

**Descripción**: Parsea una línea de restricción y extrae coeficientes, operador y lado derecho.

**Parámetros**:
- `line` (str): La restricción completa, ej. "6x1 + 3x2 <= 96".
- `var_names` (list): Lista de nombres de variables.

**Retorno**: Una tupla (coeffs, op, rhs) donde:
- `coeffs`: Diccionario de coeficientes (como en `parse_expr`).
- `op`: Operador ("<=", ">=", "=").
- `rhs`: Lado derecho como `Fraction`.

**Lógica**:
- Busca los operadores >=, <=, = en la línea.
- Divide la línea en lado izquierdo y derecho.
- Parsea el lado izquierdo con `parse_expr`.
- Convierte el lado derecho a `Fraction`.

**Excepciones**: Lanza `ValueError` si no encuentra un operador válido.

**Ejemplo**:
```python
parse_constraint("6x1 + 3x2 <= 96", ["x1", "x2"])  # ({"x1": 6, "x2": 3}, "<=", 96)
```

## Función: `solve_gran_m(maximizar, n_orig, fo_str, constraint_lines)`

**Descripción**: Implementa el algoritmo del Método de la Gran M para resolver el problema de PL.

**Parámetros**:
- `maximizar` (bool): True para maximización, False para minimización.
- `n_orig` (int): Número de variables originales.
- `fo_str` (str): Función objetivo, ej. "5x1 + 4x2".
- `constraint_lines` (list): Lista de strings con restricciones.

**Retorno**: Una tupla (iterations, result) donde:
- `iterations`: Lista de diccionarios con datos de cada iteración.
- `result`: Diccionario con el resultado final ("status", "sol", "z_real", etc.).

**Lógica**:
1. Parsea la FO y restricciones.
2. Ajusta restricciones con RHS negativo.
3. Agrega variables de holgura, exceso y artificiales según operadores.
4. Inicializa el tableau simplex.
5. Itera hasta optimalidad:
   - Calcula Zj y Cj-Zj.
   - Selecciona variable entrante (max Cj-Zj > 0).
   - Selecciona variable saliente (min ratio > 0).
   - Pivotea y actualiza.
6. Verifica factibilidad y extrae solución.

**Estados posibles**:
- "optimal": Solución encontrada.
- "infeasible": Problema infactible.
- "unbounded": Problema no acotado.
- "max_iter": Límite de iteraciones alcanzado.

## Función: `fmt_frac(val)`

**Descripción**: Formatea un valor (Fraction, int, float) para mostrar en la GUI.

**Parámetros**:
- `val`: El valor a formatear.

**Retorno**: String formateado.

**Lógica**:
- Si es Fraction con denominador 1, devuelve numerador.
- Si no, formatea como float con 4 decimales, eliminando ceros innecesarios.
- Para valores grandes (>900,000), devuelve "+M" o "-M".
- Para enteros, devuelve como string.

**Ejemplo**:
```python
fmt_frac(Fraction(5,2))  # "2.5"
fmt_frac(1000000)       # "+M"
```


## Función: `styled_item(text, bg=None, fg=TEXT_MAIN, bold=False, center=True)`

**Descripción**: Crea un `QTableWidgetItem` estilizado para las tablas de la GUI.

**Parámetros**:
- `text` (str): Texto del item.
- `bg` (str, opcional): Color de fondo.
- `fg` (str): Color de texto.
- `bold` (bool): Si el texto es negrita.
- `center` (bool): Si centrar el texto.

**Retorno**: `QTableWidgetItem` configurado.

**Lógica**:
- Crea el item con texto.
- Alinea al centro si `center=True`.
- Establece colores y fuente.
- Hace el item no editable.</content>
<parameter name="filePath">/home/giosreina/Documentos/SextoSemestre/IO1/proyecto/README.md