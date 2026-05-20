## Arquitectura de Software

El proyecto implementa una aplicación de escritorio para resolver problemas de optimización utilizando técnicas de Programación Dinámica. La arquitectura sigue un patrón Modelo-Vista-Controlador (MVC) monolítico:

- **Modelo**: La clase `ModeloPD` contiene métodos estáticos que implementan distintos algoritmos de programación dinámica (mochila 0/1, mochila ilimitada, asignación de recursos, camino óptimo en DAG). Cada método recibe parámetros primitivos y retorna un diccionario con la tabla DP, la solución óptima, la traza de decisiones y metadatos.
- **Vista**: La interfaz gráfica de usuario (GUI) está construida con PyQt6, utilizando widgets como `QMainWindow`, `QWidget`, `QTableWidget`, `QComboBox`, `QSpinBox`, etc., para mostrar entradas, la tabla DP, pasos iterativos y resultados finales.
- **Controlador**: Clases como `ItemTableWidget`, `MatrizTableWidget`, `GrafoTableWidget` y otras manejan la interacción del usuario, recopilando entradas y disparando la resolución del problema mediante la clase `ModeloPD`.

El flujo de ejecución comienza en la GUI, donde el usuario selecciona un algoritmo e ingresa datos, luego se invoca el método correspondiente de `ModeloPD` para calcular la solución, y finalmente se muestran la tabla DP, el camino óptimo y resultados en tablas y texto formateado.

## Librerías Utilizadas

- **sys**: Para manejo del sistema y argumentos de línea de comandos.
- **PyQt6.QtWidgets**: Para crear la interfaz gráfica, incluyendo ventanas, botones, tablas, spinboxes, comboboxes y layouts.
- **PyQt6.QtCore**: Para señales, hilos y utilidades básicas de Qt, como `Qt.AlignmentFlag` y constants.
- **PyQt6.QtGui**: Para elementos gráficos como fuentes y colores utilizados en el estilo de la aplicación.

## Clase: `ModeloPD`

**Descripción**: Clase contenedora de métodos estáticos que implementan los algoritmos de Programación Dinámica. Cada método es autónomo y recibe parámetros primitivos (listas, enteros, cadenas), realizando toda la lógica de DP sin dependencias externas de GUI.

---

## Método: `ModeloPD.mochila_01(valores, pesos, W, tipo, minimos=None)`

**Descripción**: Resuelve el problema clásico de la mochila 0/1 mediante programación dinámica. Cada ítem puede ser incluido (1) o no incluido (0), exactamente una sola vez.

**Parámetros**:
- `valores` (list of int/float): Valor de cada ítem, ej. `[3, 4, 5, 6]`.
- `pesos` (list of int/float): Peso de cada ítem, ej. `[2, 3, 4, 5]`.
- `W` (int): Capacidad máxima de la mochila, ej. `10`.
- `tipo` (str): `'max'` para maximizar valor o `'min'` para minimizar peso.
- `minimos` (list of int/float, opcional): Valor mínimo que debe aportar cada ítem para ser considerado. Si es None, se asume `[0, 0, ..., 0]`.

**Retorno**: Diccionario con:
- `algoritmo`: Nombre del algoritmo.
- `recurrencia`: Fórmula de la recurrencia.
- `tipo`: Tipo de optimización aplicado.
- `optimo`: Valor óptimo de la solución (suma de valores o mínimo peso).
- `seleccionados`: Índices de ítems incluidos en la solución.
- `peso_usado`: Peso total utilizado.
- `capacidad`: Capacidad de la mochila.
- `n`: Número de ítems.
- `valores`, `pesos`: Copias de los parámetros de entrada.
- `dp`: Tabla DP bidimensional (n+1) × (W+1).
- `dim`, `filas`, `columnas`: Metadatos para visualización.
- `pasos`: Lista de pasos iterativos para visualizar la construcción de la solución.
- `factible`: Boolean indicando si existe una solución válida.
- `path`: Conjunto de celdas (i, w) que forman parte del camino óptimo.

**Recurrencia**:
```
dp[i][w] = max/min( dp[i-1][w], dp[i-1][w-p[i]] + v[i] )
```
Donde:
- `dp[i][w]` = valor óptimo usando los primeros `i` ítems con capacidad `w`.
- `dp[i-1][w]` = opción de no incluir el ítem `i`.
- `dp[i-1][w-p[i]] + v[i]` = opción de incluir el ítem `i` (si cabe).

**Complejidad**: O(n · W) en tiempo; O(n · W) en espacio.

**Lógica**:
1. Inicializa tabla DP de tamaño (n+1) × (W+1).
2. Itera sobre cada ítem `i` y cada capacidad `w`.
3. Decide si incluir o no el ítem `i` comparando ambas opciones.
4. Registra decisiones en `pasos` para visualización.
5. Reconstruye el conjunto de ítems seleccionados mediante backtracking desde `dp[n][W]`.
6. Marca el camino óptimo en `path`.

**Ejemplo**:
```python
resultado = ModeloPD.mochila_01(
    valores=[3, 4, 5, 6],
    pesos=[2, 3, 4, 5],
    W=10,
    tipo='max'
)
# resultado['optimo'] = 13 (ítems 0, 1, 3: valores 3+4+6, pesos 2+3+5)
# resultado['seleccionados'] = [0, 1, 3]
```

---

## Método: `ModeloPD.mochila_ilimitada(valores, pesos, W, tipo, minimos=None)`

**Descripción**: Resuelve el problema de la mochila ilimitada (unbounded knapsack). Cada ítem puede ser incluido múltiples veces sin límite.

**Parámetros**:
- `valores` (list of int/float): Valor de cada ítem reutilizable.
- `pesos` (list of int/float): Peso de cada ítem reutilizable.
- `W` (int): Capacidad máxima de la mochila.
- `tipo` (str): `'max'` para maximizar valor o `'min'` para minimizar peso.
- `minimos` (list of int/float, opcional): Valor mínimo requerido de cada ítem para ser considerado.

**Retorno**: Diccionario con:
- `algoritmo`: "Mochila Ilimitada".
- `recurrencia`: Fórmula de recurrencia para problema ilimitado.
- `tipo`: Tipo de optimización.
- `optimo`: Valor óptimo.
- `usados`: Diccionario {índice_item: cantidad} con la cantidad de veces que se usa cada ítem.
- `capacidad`, `n`: Capacidad y número de ítems únicos.
- `valores`, `pesos`: Copias de entrada.
- `dp`: Tabla DP unidimensional de tamaño W+1.
- `dim`, `filas`, `columnas`: Metadatos para visualización.
- `pasos`: Registro de decisiones.
- `factible`: Boolean indicando factibilidad.
- `path`: Conjunto con la capacidad utilizada.

**Recurrencia**:
```
dp[w] = max/min { dp[w - p[i]] + v[i] }  ∀ i ∈ {0, ..., n-1}
```
Donde:
- `dp[w]` = valor óptimo con capacidad exacta `w`.
- La decisión es elegir cuál ítem usar y restar su peso `p[i]`.
- El problema es ilimitado: un mismo ítem puede elegirse múltiples veces.

**Complejidad**: O(n · W) en tiempo; O(W) en espacio.

**Lógica**:
1. Inicializa vector DP unidimensional `dp[0..W]` con 0 en `dp[0]` e infinito negativo en los demás (para maximización).
2. Por cada capacidad `w` de 1 a W:
   - Prueba cada ítem `i`.
   - Si el ítem cabe (`p[i] ≤ w`), calcula `dp[w-p[i]] + v[i]`.
   - Actualiza `dp[w]` si esta opción es mejor.
   - Registra qué ítem fue elegido en `desde[w]`.
3. Reconstruye la cantidad de cada ítem usado mediante backtracking.
4. Marca W como parte del camino óptimo.

**Ejemplo**:
```python
resultado = ModeloPD.mochila_ilimitada(
    valores=[3, 4, 5],
    pesos=[2, 3, 4],
    W=10,
    tipo='max'
)
# resultado['optimo'] = 15 (usar 5 veces el ítem 0: 5 × 3 = 15, peso = 5 × 2 = 10)
# resultado['usados'] = {0: 5, 1: 0, 2: 0}
```

---

## Método: `ModeloPD.tabla_personalizada(matriz, tipo, min_x=None)`

**Descripción**: Resuelve un problema general de asignación de recursos multi-etapa mediante DP. Utiliza propagación hacia adelante con estados representados por recurso disponible.

**Parámetros**:
- `matriz` (list of list): Tabla de retornos donde `matriz[e][x]` = retorno de asignar `x` unidades de recurso a la etapa `e`. Dimensión: `etapas × (W+1)`.
- `tipo` (str): `'max'` para maximizar retorno total o `'min'` para minimizar costo total.
- `min_x` (list of int, opcional): Mínimo de unidades que DEBE recibir cada etapa. Por defecto es `[0, 0, ..., 0]`.

**Retorno**: Diccionario con:
- `algoritmo`: "Tabla Personalizada".
- `recurrencia`: Fórmula de recurrencia multi-etapa.
- `tipo`: Tipo de optimización.
- `optimo`: Valor óptimo total (suma acumulada de retornos).
- `camino`: Lista de estados (recurso disponible) al inicio de cada etapa.
- `asignaciones`: Lista de decisiones `x` tomadas en cada etapa.
- `retornos`: Valor de `matriz[e][x]` para cada etapa según la solución óptima.
- `dp`: Tabla DP bidimensional `etapas × (W+1)` con valores óptimos.
- `dim`, `filas`, `columnas`: Metadatos.
- `pasos`: Registro de decisiones por etapa.
- `factible`: Boolean.
- `path`: Conjunto de celdas (e, s) del camino óptimo.
- `min_x`: Copias de mínimos por etapa.
- `error`: (si aplica) Mensaje de error si los mínimos son infactibles.

**Recurrencia**:
```
Etapa final (e = E-1):
  f[E-1][s] = max/min { matriz[E-1][x] }  para x ∈ [min_x[E-1]..s]

Etapas anteriores (e < E-1):
  f[e][s] = max/min { matriz[e][x] + f[e+1][s-x] }  para x ∈ [min_x[e]..s]
```

Donde:
- `s` = recurso disponible al inicio de la etapa `e`.
- `x` = decisión: unidades asignadas a la etapa `e`.
- El recurso que pasa a la siguiente etapa es `s - x`.

**Complejidad**: O(E · W²) en tiempo; O(E · W) en espacio.

**Lógica**:
1. Verifica que la suma de mínimos no supere el recurso total W.
2. Inicializa tabla DP `f[e][s]` y tabla de decisiones `dec[e][s]`.
3. Rellena la etapa final (e = E-1) iterando sobre todos los estados posibles.
4. Itera hacia atrás (e = E-2, E-3, ..., 0) llenando la tabla DP.
5. Para cada estado `s`, prueba todas las decisiones `x` válidas y toma la mejor.
6. Reconstruye el camino óptimo mediante traza hacia adelante desde estado inicial.
7. Calcula el conjunto de celdas del camino óptimo.

**Validaciones**:
- Si `sum(min_x) > W`, retorna error indicando infactibilidad.

**Ejemplo**:
```python
matriz = [
    [0, 10, 20, 30, 40],     # Etapa 1: retornos por unidades asignadas
    [0, 8, 18, 26, 35],      # Etapa 2
    [0, 12, 22, 30, 38],     # Etapa 3
]
resultado = ModeloPD.tabla_personalizada(
    matriz=matriz,
    tipo='max',
    min_x=[1, 1, 1]
)
# Asigna recurso total de 4 entre 3 etapas con mínimos [1, 1, 1]
# resultado['optimo'] = suma óptima de retornos
```

---

## Método: `ModeloPD.camino_dag(n_nodos, aristas, origen, destino, tipo)`

**Descripción**: Encuentra el camino óptimo (máximo o mínimo peso) en un Grafo Acíclico Dirigido (DAG) usando DP con ordenamiento topológico.

**Parámetros**:
- `n_nodos` (int): Número de nodos en el grafo, ej. `5`.
- `aristas` (list of tuple): Lista de aristas `(desde, a, peso)`, ej. `[(0, 1, 5), (0, 2, 3), ...]`.
- `origen` (int): Nodo inicial, ej. `0`.
- `destino` (int): Nodo final deseado, ej. `4`.
- `tipo` (str): `'max'` para maximizar peso total o `'min'` para minimizar.

**Retorno**: Diccionario con:
- `algoritmo`: "Camino en DAG".
- `recurrencia`: Fórmula de recurrencia para distancias.
- `tipo`: Tipo de optimización.
- `optimo`: Peso total del camino óptimo (None si no existe camino).
- `camino`: Lista de nodos que forman el camino óptimo desde origen a destino.
- `n_nodos`: Número de nodos.
- `dp`: Vector DP de tamaño n_nodos con distancias óptimas desde origen.
- `dim`, `filas`, `columnas`: Metadatos.
- `pasos`: Registro de relajaciones de aristas.
- `factible`: Boolean (True si existe camino).
- `path`: Conjunto de nodos que forman el camino óptimo.
- `error`: (si aplica) Mensaje de error si el grafo tiene ciclos.

**Recurrencia**:
```
dist[v] = max/min { dist[u] + w(u, v) }  para todo u → v
```

Donde:
- `dist[v]` = distancia óptima desde origen a nodo `v`.
- `w(u, v)` = peso de la arista desde `u` a `v`.
- El cálculo se realiza en orden topológico para garantizar que `dist[u]` esté finalizado antes de procesar sus sucesores.

**Complejidad**: O(V + E) en tiempo (debido al ordenamiento topológico); O(V) en espacio.

**Lógica**:
1. Construye lista de adyacencia a partir de las aristas.
2. Calcula grados de entrada de cada nodo.
3. Realiza ordenamiento topológico usando BFS (algoritmo de Kahn).
4. Verifica que el grafo sea acíclico (número de nodos procesados = n_nodos).
5. Inicializa distancias: `dist[origen] = 0`, el resto en `-infinito` (para max) o `+infinito` (para min).
6. Procesa nodos en orden topológico, relajando todas sus aristas salientes.
7. Reconstruye el camino óptimo mediante backtracking desde destino hacia origen.
8. Marca los nodos del camino en `path`.

**Validaciones**:
- Si el grafo tiene ciclos, retorna error "El grafo tiene un ciclo. Ingrese un DAG."

**Ejemplo**:
```python
aristas = [
    (0, 1, 5),
    (0, 2, 3),
    (1, 3, 2),
    (2, 3, 6),
    (3, 4, 4),
]
resultado = ModeloPD.camino_dag(
    n_nodos=5,
    aristas=aristas,
    origen=0,
    destino=4,
    tipo='min'
)
# resultado['optimo'] = 13 (camino: 0 → 1 → 3 → 4, pesos: 5 + 2 + 4)
# resultado['camino'] = [0, 1, 3, 4]
```

---

## Estructura de Retorno: Diccionarios de Solución

Todos los métodos de `ModeloPD` retornan un diccionario con estructura consistente para facilitar visualización:

### Campos Comunes

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `algoritmo` | str | Nombre del algoritmo usado |
| `recurrencia` | str | Fórmula matemática de la DP |
| `tipo` | str | `'max'` o `'min'` |
| `optimo` | int/float/None | Valor óptimo de la solución |
| `factible` | bool | Si la solución es válida |
| `dp` | list | Tabla DP (1D o 2D) con valores óptimos |
| `dim` | str | `'1d'` o `'2d'` (dimensionalidad) |
| `filas` | list | Etiquetas de filas para visualización |
| `columnas` | list | Etiquetas de columnas para visualización |
| `pasos` | list | Registro de decisiones por etapa/iteración |
| `path` | set | Conjunto de celdas/nodos que forman el camino óptimo |

### Campos Específicos por Algoritmo

- **mochila_01, mochila_ilimitada**: `seleccionados`, `peso_usado`, `capacidad`, `usados`, `valores`, `pesos`.
- **tabla_personalizada**: `camino`, `asignaciones`, `retornos`, `min_x`.
- **camino_dag**: `camino`, `n_nodos`.

---

## Validación de Entrada

Todos los métodos de `ModeloPD` asumen que los parámetros son válidos (tipos correctos, valores positivos donde corresponda). La aplicación GUI realiza validación previa para garantizar:
- Listas no vacías.
- W, n_nodos, etapas > 0.
- Operador es uno de `{'max', 'min'}`.
- Grafo sin ciclos (para camino_dag).

---

## Ejemplo de Integración GUI-Modelo

```python
# En la GUI del usuario
tipo_op = "max"  # Seleccionado del combobox
valores = [3, 4, 5, 6]
pesos = [2, 3, 4, 5]
capacidad = 10

# Se invoca el modelo
resultado = ModeloPD.mochila_01(valores, pesos, capacidad, tipo_op)

# La GUI itera sobre resultado['pasos'] para mostrar tabla de progreso
# La GUI accede a resultado['dp'] para mostrar la tabla DP
# La GUI construye la ruta usando resultado['path'] y la colorea en verde
# La GUI muestra resultado['seleccionados'] como solución
```
