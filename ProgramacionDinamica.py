import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QComboBox, QSpinBox, QPushButton,
    QTableWidget, QTableWidgetItem, QScrollArea, QFrame,
    QHeaderView, QGroupBox, QTextEdit, QSplitter,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

class ModeloPD:
    """
    Contiene todos los algoritmos de Programación Dinámica.
    Cada método recibe datos primitivos y devuelve un dict con
    la tabla DP, la solución óptima y la traza de decisiones.
    """

    @staticmethod
    def mochila_01(valores: list, pesos: list, W: int, tipo: str,
                   minimos: list = None) -> dict:
        """
        Cada ítem se usa 0 o 1 vez.
        Recurrencia: dp[i][w] = max/min(dp[i-1][w], dp[i-1][w-p[i]] + v[i])
        minimos[i]: valor mínimo que debe aportar el ítem i para ser considerado.
        Complejidad: O(n·W)
        """
        n = len(valores)
        INF = float('inf')
        if minimos is None:
            minimos = [0] * n

        dp = [[0] * (W + 1) for _ in range(n + 1)]
        if tipo == 'min':
            for i in range(n + 1):
                for w in range(W + 1):
                    dp[i][w] = INF
            for i in range(n + 1):
                dp[i][0] = 0

        pasos = []
        for i in range(1, n + 1):
            vi, pi = valores[i - 1], pesos[i - 1]
            for w in range(W + 1):
                dp[i][w] = dp[i - 1][w]
                decision = "no incluir"
                if pi <= w and vi >= minimos[i - 1]:
                    prev = dp[i - 1][w - pi]
                    if prev != INF:
                        cand = prev + vi
                        if tipo == 'max' and cand > dp[i][w]:
                            dp[i][w] = cand
                            decision = "incluir"
                        elif tipo == 'min' and cand < dp[i][w]:
                            dp[i][w] = cand
                            decision = "incluir"
                if w == W:
                    pasos.append({
                        "etapa": f"Ítem {i}  v={vi} p={pi}",
                        "estado": f"w={w}",
                        "valor": dp[i][w] if dp[i][w] != INF else None,
                        "decision": decision,
                    })

        sel, w_rem = [], W
        for i in range(n, 0, -1):
            if dp[i][w_rem] != dp[i - 1][w_rem]:
                sel.append(i - 1)
                w_rem -= pesos[i - 1]
        sel.reverse()

        path = set()
        w = W
        for i in range(n, 0, -1):
            path.add((i, w))
            if dp[i][w] != dp[i - 1][w]:
                w -= pesos[i - 1]
        path.add((0, w))

        optimo = dp[n][W]
        dp_j = [[None if x == INF else x for x in r] for r in dp]
        return {
            "algoritmo": "Mochila 0/1",
            "recurrencia": f"dp[i][w] = {tipo}( dp[i-1][w],  dp[i-1][w-p[i]] + v[i] )",
            "tipo": tipo,
            "optimo": None if optimo == INF else optimo,
            "seleccionados": sel,
            "peso_usado": sum(pesos[i] for i in sel),
            "capacidad": W, "n": n,
            "valores": valores, "pesos": pesos,
            "dp": dp_j, "dim": "2d",
            "filas": ["Vacío"] + [f"I{i+1}" for i in range(n)],
            "columnas": [str(w) for w in range(W + 1)],
            "pasos": pasos,
            "factible": optimo != INF,
            "path": path,
        }

    @staticmethod
    def mochila_ilimitada(valores: list, pesos: list, W: int, tipo: str,
                          minimos: list = None) -> dict:
        """
        Ítems reutilizables sin límite.
        Recurrencia: dp[w] = max/min{ dp[w-p[i]] + v[i] }  ∀ i
        Complejidad: O(n·W)
        """
        n = len(valores)
        INF = float('inf')
        if minimos is None:
            minimos = [0] * n

        dp = [0] + ([-INF if tipo == 'max' else INF] * W)
        desde = [-1] * (W + 1)
        pasos = []

        for w in range(1, W + 1):
            for i in range(n):
                if pesos[i] <= w and valores[i] >= minimos[i]:
                    prev = dp[w - pesos[i]]
                    if abs(prev) == INF:
                        continue
                    cand = prev + valores[i]
                    if tipo == 'max' and cand > dp[w]:
                        dp[w] = cand
                        desde[w] = i
                    elif tipo == 'min' and cand < dp[w]:
                        dp[w] = cand
                        desde[w] = i
            if desde[w] != -1:
                i = desde[w]
                pasos.append({
                    "etapa": f"w={w}",
                    "estado": f"I{i+1}",
                    "valor": dp[w] if abs(dp[w]) != INF else None,
                    "decision": f"usar I{i+1} (v={valores[i]}, p={pesos[i]})",
                })

        usados: dict = {}
        rem = W
        while rem > 0 and desde[rem] != -1:
            i = desde[rem]
            usados[i] = usados.get(i, 0) + 1
            rem -= pesos[i]

        optimo = dp[W]
        dp_j = [None if abs(x) == INF else x for x in dp]
        return {
            "algoritmo": "Mochila Ilimitada",
            "recurrencia": f"dp[w] = {tipo}{{ dp[w-p[i]] + v[i] }}  ∀ i",
            "tipo": tipo,
            "optimo": None if abs(optimo) == INF else optimo,
            "usados": usados,
            "capacidad": W, "n": n,
            "valores": valores, "pesos": pesos,
            "dp": dp_j, "dim": "1d",
            "filas": ["dp[w]"],
            "columnas": [str(w) for w in range(W + 1)],
            "pasos": pasos,
            "factible": abs(optimo) != INF,
            "path": {W},
        }

    @staticmethod
    def tabla_personalizada(matriz: list, tipo: str,
                            min_x: list = None) -> dict:
        """
        DP de asignación de recursos multi-etapa con restricciones mínimas.

        matriz[e][x] = retorno de asignar x unidades de recurso a la etapa e.
        min_x[e]     = mínimo de unidades que DEBE recibir la etapa e.
        W            = recurso total = len(matriz[0]) - 1

        Recurrencia (propagación hacia adelante, llenado hacia atrás):
          Última etapa:
            f[E-1][s] = max/min{ matriz[E-1][x] }
                        para x in [min_x[E-1] .. s]

          Etapas anteriores:
            f[e][s] = max/min{ matriz[e][x] + f[e+1][s-x] }
                      para x in [min_x[e] .. s]

        El estado s = recurso disponible al inicio de la etapa e.
        La decisión x = unidades asignadas a la etapa e.
        El recurso que pasa a etapas siguientes = s - x.

        El valor óptimo final es f[0][W] = suma acumulada de todos los retornos.
        Complejidad: O(etapas · W²)
        """
        etapas = len(matriz)
        W = len(matriz[0]) - 1
        INF = float('inf')

        if min_x is None:
            min_x = [0] * etapas

        total_min = sum(min_x)
        if total_min > W:
            return {
                "error": f"La suma de mínimos ({total_min}) supera el recurso total ({W}).",
                "factible": False,
            }

        mejor_init = -INF if tipo == 'max' else INF
        f   = [[mejor_init] * (W + 1) for _ in range(etapas)]
        dec = [[-1]         * (W + 1) for _ in range(etapas)]

        e = etapas - 1
        lo = min_x[e]
        for s in range(W + 1):
            for x in range(lo, s + 1):
                val = matriz[e][x]
                if tipo == 'max' and val > f[e][s]:
                    f[e][s] = val
                    dec[e][s] = x
                elif tipo == 'min' and val < f[e][s]:
                    f[e][s] = val
                    dec[e][s] = x

        for e in range(etapas - 2, -1, -1):
            lo = min_x[e]
            for s in range(W + 1):
                for x in range(lo, s + 1):
                    s_rest = s - x
                    fut = f[e + 1][s_rest]
                    if abs(fut) == INF:
                        continue
                    cand = matriz[e][x] + fut
                    if tipo == 'max' and cand > f[e][s]:
                        f[e][s] = cand
                        dec[e][s] = x
                    elif tipo == 'min' and cand < f[e][s]:
                        f[e][s] = cand
                        dec[e][s] = x

        optimo = f[0][W]
        factible = abs(optimo) != INF

        asignaciones = []
        pasos = []
        camino = []
        s_cur = W
        for e in range(etapas):
            camino.append(s_cur)
            x_opt = dec[e][s_cur] if dec[e][s_cur] != -1 else 0
            asignaciones.append(x_opt)
            pasos.append({
                "etapa":    f"E{e+1}",
                "estado":   f"s={s_cur}",
                "valor":    matriz[e][x_opt],
                "decision": f"asignar x={x_opt}  |  resta={s_cur - x_opt}",
            })
            s_cur -= x_opt

        f_j = [[None if abs(v) == INF else v for v in row] for row in f]

        path = set()
        s_p = W
        for e in range(etapas):
            path.add((e, s_p))
            s_p -= dec[e][s_p] if dec[e][s_p] != -1 else 0

        return {
            "algoritmo":    "Tabla Personalizada",
            "recurrencia":  f"f[e][s] = {tipo}{{ r[e][x] + f[e+1][s-x] }}  x ∈ [min_x..s]",
            "tipo":         tipo,
            "optimo":       None if abs(optimo) == INF else optimo,
            "camino":       camino,
            "asignaciones": asignaciones,
            "retornos":     [matriz[e][asignaciones[e]] for e in range(etapas)],
            "dp":           f_j,  "dim": "2d",
            "filas":        [f"E{e+1}" for e in range(etapas)],
            "columnas":     [str(s) for s in range(W + 1)],
            "pasos":        pasos,
            "factible":     factible,
            "path":         path,
            "min_x":        min_x,
        }

    @staticmethod
    def camino_dag(n_nodos: int, aristas: list, origen: int,
                   destino: int, tipo: str) -> dict:
        """
        Camino óptimo en grafo acíclico dirigido.
        Recurrencia: dist[v] = min/max{ dist[u] + w(u,v) }
        Complejidad: O(V + E)
        """
        INF = float('inf')
        adj = {i: [] for i in range(n_nodos)}
        in_deg = [0] * n_nodos
        for de, a, w in aristas:
            adj[de].append((a, w))
            in_deg[a] += 1

        cola = [i for i in range(n_nodos) if in_deg[i] == 0]
        topo = []
        while cola:
            u = cola.pop(0)
            topo.append(u)
            for v, _ in adj[u]:
                in_deg[v] -= 1
                if in_deg[v] == 0:
                    cola.append(v)

        if len(topo) != n_nodos:
            return {"error": "El grafo tiene un ciclo. Ingrese un DAG.", "factible": False}

        dist = [-INF if tipo == 'max' else INF] * n_nodos
        dist[origen] = 0
        padre = [-1] * n_nodos
        pasos = []

        for u in topo:
            if abs(dist[u]) == INF:
                continue
            for v, w in adj[u]:
                cand = dist[u] + w
                if tipo == 'max' and cand > dist[v]:
                    dist[v] = cand
                    padre[v] = u
                    pasos.append({"etapa": f"{u}→{v}", "estado": str(v),
                                  "valor": cand, "decision": f"vía nodo {u} (w={w})"})
                elif tipo == 'min' and cand < dist[v]:
                    dist[v] = cand
                    padre[v] = u
                    pasos.append({"etapa": f"{u}→{v}", "estado": str(v),
                                  "valor": cand, "decision": f"vía nodo {u} (w={w})"})

        camino = []
        cur = destino
        while cur != -1:
            camino.insert(0, cur)
            cur = padre[cur]

        optimo = dist[destino]
        dp_j = [None if abs(x) == INF else x for x in dist]
        return {
            "algoritmo": "Camino en DAG",
            "recurrencia": f"dist[v] = {tipo}{{ dist[u] + w(u,v) }}",
            "tipo": tipo,
            "optimo": None if abs(optimo) == INF else optimo,
            "camino": camino if camino and camino[0] == origen else [],
            "n_nodos": n_nodos,
            "dp": dp_j, "dim": "1d",
            "filas": ["dist[v]"],
            "columnas": [str(v) for v in range(n_nodos)],
            "pasos": pasos,
            "factible": abs(optimo) != INF,
            "path": set(camino) if camino else set(),
        }

C = {
    "bg_deep":  "#090c10",
    "bg_panel": "#0e1219",
    "bg_card":  "#131820",
    "bg_input": "#192030",
    "accent":   "#00aaff",
    "accent2":  "#f0a500",
    "accent3":  "#00e676",
    "accent4":  "#ff6b6b",
    "text_p":   "#cdd9e8",
    "text_s":   "#5d7a93",
    "text_m":   "#2e4257",
    "border":   "#1a2a3a",
    "border_a": "#08405e",
}

QSS = f"""
* {{ font-family: 'Segoe UI', 'Arial', sans-serif; font-size: 12px; }}
QMainWindow, QWidget {{ background-color: {C['bg_deep']}; color: {C['text_p']}; }}
QGroupBox {{
    background-color: {C['bg_panel']}; border: 1px solid {C['border']};
    border-radius: 4px; margin-top: 10px; padding-top: 10px;
    color: {C['accent']}; font-size: 9px; font-weight: bold; letter-spacing: 2px;
}}
QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 4px; }}
QLabel {{ color: {C['text_s']}; font-size: 11px; }}
QComboBox {{
    background-color: {C['bg_input']}; border: 1px solid {C['border_a']};
    color: {C['text_p']}; padding: 4px 8px; border-radius: 3px; min-width: 130px;
}}
QComboBox:focus {{ border-color: {C['accent']}; }}
QComboBox::drop-down {{ border: none; width: 16px; }}
QComboBox QAbstractItemView {{
    background-color: {C['bg_panel']}; color: {C['text_p']};
    selection-background-color: {C['border_a']}; border: 1px solid {C['border_a']};
}}
QSpinBox {{
    background-color: {C['bg_input']}; border: 1px solid {C['border_a']};
    color: {C['text_p']}; padding: 4px 6px; border-radius: 3px;
    font-family: 'Courier New', monospace; min-width: 60px;
}}
QSpinBox:focus {{ border-color: {C['accent']}; }}
QSpinBox::up-button, QSpinBox::down-button {{ background: {C['bg_panel']}; border: none; width: 14px; }}
QTextEdit {{
    background-color: {C['bg_input']}; border: 1px solid {C['border_a']};
    color: {C['text_p']}; padding: 5px 8px; border-radius: 3px;
    font-family: 'Courier New', monospace; font-size: 11px;
}}
QTextEdit:focus {{ border-color: {C['accent']}; }}
QPushButton {{
    background-color: transparent; border: 1px solid {C['border']};
    color: {C['text_s']}; padding: 6px 14px; border-radius: 3px;
    font-size: 10px; font-weight: bold; letter-spacing: 2px;
}}
QPushButton:hover {{ border-color: {C['text_s']}; color: {C['text_p']}; }}
QPushButton
QPushButton
QPushButton
QPushButton
QPushButton
QPushButton
QTableWidget {{
    background-color: {C['bg_card']}; border: 1px solid {C['border']};
    gridline-color: {C['border']}; color: {C['text_s']};
    font-family: 'Courier New', monospace; font-size: 10px;
    selection-background-color: rgba(0,170,255,40); selection-color: {C['text_p']};
}}
QTableWidget::item {{ padding: 3px 6px; }}
QHeaderView::section {{
    background-color: {C['bg_panel']}; color: {C['accent']}; border: none;
    border-right: 1px solid {C['border']}; border-bottom: 1px solid {C['border_a']};
    padding: 4px 8px; font-size: 9px; letter-spacing: 1px;
    font-family: 'Courier New', monospace; font-weight: normal;
}}
QScrollArea {{ border: none; background: transparent; }}
QScrollBar:vertical {{ background: {C['bg_deep']}; width: 6px; border: none; margin: 0; }}
QScrollBar::handle:vertical {{ background: {C['border_a']}; border-radius: 3px; min-height: 24px; }}
QScrollBar::handle:vertical:hover {{ background: {C['accent']}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; border: none; }}
QScrollBar:horizontal {{ background: {C['bg_deep']}; height: 6px; border: none; margin: 0; }}
QScrollBar::handle:horizontal {{ background: {C['border_a']}; border-radius: 3px; min-width: 24px; }}
QScrollBar::handle:horizontal:hover {{ background: {C['accent']}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; border: none; }}
QSplitter::handle {{ background: {C['border']}; }}
QFrame
QFrame
QFrame
QFrame
    border-left: 2px solid {C['accent2']}; border-radius: 4px; }}
"""

class ItemTableWidget(QWidget):
    """Tabla editable: valor, peso y mínimo por ítem (mochilas)."""

    _DEF_V = [3, 4, 5, 6, 2, 7, 1, 8, 3, 5, 4, 6]
    _DEF_P = [2, 3, 4, 5, 1, 3, 2, 6, 2, 4, 1, 3]

    def __init__(self, n: int = 4, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(5)

        self._tbl = QTableWidget()
        self._tbl.setColumnCount(3)
        self._tbl.setHorizontalHeaderLabels(["Ítem", "Valor", "Peso"])
        self._tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._tbl.verticalHeader().setVisible(False)
        lay.addWidget(self._tbl)

        lbl = QLabel("Valor mínimo por ítem (opcional):")
        lbl.setStyleSheet(f"color:{C['text_m']}; font-size:9px; font-family:'Courier New';")
        lay.addWidget(lbl)
        self._tbl_min = QTableWidget()
        self._tbl_min.setFixedHeight(50)
        lay.addWidget(self._tbl_min)

        self.rebuild(n)

    def rebuild(self, n: int):
        self._tbl.setRowCount(n)
        for i in range(n):
            lbl = QTableWidgetItem(f"I{i+1}")
            lbl.setForeground(QColor(C["accent2"]))
            lbl.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self._tbl.setItem(i, 0, lbl)
            self._tbl.setItem(i, 1, QTableWidgetItem(str(self._DEF_V[i] if i < len(self._DEF_V) else i+1)))
            self._tbl.setItem(i, 2, QTableWidgetItem(str(self._DEF_P[i] if i < len(self._DEF_P) else 1)))
        self._tbl.setFixedHeight(min(n * 27 + 32, 260))

        self._tbl_min.setRowCount(1)
        self._tbl_min.setColumnCount(n)
        self._tbl_min.setHorizontalHeaderLabels([f"I{i+1}" for i in range(n)])
        self._tbl_min.verticalHeader().setVisible(False)
        self._tbl_min.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        for i in range(n):
            self._tbl_min.setItem(0, i, QTableWidgetItem("0"))

    def get_data(self) -> tuple:
        n = self._tbl.rowCount()
        vals, pesos = [], []
        for i in range(n):
            vt = self._tbl.item(i, 1)
            pt = self._tbl.item(i, 2)
            vals.append(int(vt.text()) if vt and vt.text().lstrip('-').isdigit() else 1)
            pesos.append(max(1, int(pt.text())) if pt and pt.text().lstrip('-').isdigit() else 1)
        minimos = [
            int(self._tbl_min.item(0, i).text())
            if self._tbl_min.item(0, i) and self._tbl_min.item(0, i).text().lstrip('-').isdigit() else 0
            for i in range(self._tbl_min.columnCount())
        ]
        return vals, pesos, minimos

class MatrizWidget(QWidget):
    """
    Tabla editable de retornos r[etapa][x_asignado] para Tabla Personalizada.
    Filas = etapas, Columnas = x = 0, 1, ..., W  (unidades asignadas a esa etapa).
    Fila adicional: mínimo de unidades que DEBE recibir cada etapa.
    """

    def __init__(self, etapas: int = 3, W: int = 10, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(5)

        lbl_r = QLabel("r[etapa][x] — retorno de asignar x unidades a cada etapa:")
        lbl_r.setStyleSheet(f"color:{C['text_m']}; font-size:9px; font-family:'Courier New';")
        lay.addWidget(lbl_r)

        self._tbl = QTableWidget()
        lay.addWidget(self._tbl)

        lbl_m = QLabel("Demanda mínima por etapa (en unidades de retorno):")
        lbl_m.setStyleSheet(f"color:{C['accent2']}; font-size:9px; font-family:'Courier New';")
        lbl_m.setWordWrap(True)
        lay.addWidget(lbl_m)

        self._tbl_min = QTableWidget()
        self._tbl_min.setFixedHeight(50)
        lay.addWidget(self._tbl_min)

        self.rebuild(etapas, W)

    def rebuild(self, etapas: int, W: int):
        cols = W + 1
        self._tbl.setRowCount(etapas)
        self._tbl.setColumnCount(cols)
        self._tbl.setHorizontalHeaderLabels([f"x={x}" for x in range(cols)])
        self._tbl.setVerticalHeaderLabels([f"E{e+1}" for e in range(etapas)])
        self._tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        for e in range(etapas):
            for x in range(cols):
                self._tbl.setItem(e, x, QTableWidgetItem("0"))
        self._tbl.setFixedHeight(min(etapas * 27 + 32, 220))

        self._tbl_min.setRowCount(1)
        self._tbl_min.setColumnCount(etapas)
        self._tbl_min.setHorizontalHeaderLabels([f"E{e+1}" for e in range(etapas)])
        self._tbl_min.verticalHeader().setVisible(False)
        self._tbl_min.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        for e in range(etapas):
            self._tbl_min.setItem(0, e, QTableWidgetItem("0"))

    def get_data(self, W_real: int = None) -> tuple:
        """
        Lee la matriz ingresada por el usuario.
        Si W_real se especifica, extiende cada fila hasta W_real columnas
        usando interpolación lineal basada en la última celda con valor > 0,
        garantizando que el modelo siempre trabaja con el W del spinbox.
        """
        rows = self._tbl.rowCount()
        cols = self._tbl.columnCount()
        matriz_raw = [
            [int(self._tbl.item(r, c).text())
             if self._tbl.item(r, c) and self._tbl.item(r, c).text().lstrip('-').isdigit() else 0
             for c in range(cols)]
            for r in range(rows)
        ]

        if W_real is not None and W_real + 1 != cols:
            matriz = []
            for fila in matriz_raw:
                if W_real + 1 <= cols:
                    matriz.append(fila[:W_real + 1])
                else:
                    vals_nz = [(x, v) for x, v in enumerate(fila) if v > 0]
                    if len(vals_nz) >= 2:
                        x1, v1 = vals_nz[-2]
                        x2, v2 = vals_nz[-1]
                        paso = (v2 - v1) / max(x2 - x1, 1)
                    elif len(vals_nz) == 1:
                        x2, v2 = vals_nz[-1]
                        paso = v2 / max(x2, 1)
                    else:
                        paso = 0
                    nueva = list(fila)
                    for x in range(cols, W_real + 1):
                        nueva.append(int(round(nueva[-1] + paso)))
                    matriz.append(nueva)
        else:
            matriz = matriz_raw

        min_x = []
        demandas = []
        for e in range(self._tbl_min.columnCount()):
            cell = self._tbl_min.item(0, e)
            demanda = int(cell.text()) if cell and cell.text().lstrip('-').isdigit() else 0
            demandas.append(demanda)
            if demanda == 0:
                min_x.append(0)
                continue
            fila = matriz[e] if e < len(matriz) else []
            x_min = len(fila) - 1
            for x, val in enumerate(fila):
                if val >= demanda:
                    x_min = x
                    break
            min_x.append(x_min)
        return matriz, min_x, demandas

class PanelResultados(QWidget):
    """Panel derecho: muestra tabla DP, solución y traza."""

    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(10)

        self._lbl_hdr = QLabel("Sin resultados")
        self._lbl_hdr.setStyleSheet(
            f"color:{C['text_s']}; font-size:9px; font-weight:bold; letter-spacing:3px;")
        root.addWidget(self._lbl_hdr)

        sub = QLabel("TABLA DP  &  SOLUCIÓN")
        sub.setStyleSheet(
            f"color:{C['accent']}; font-size:12px; font-weight:bold; letter-spacing:2px;"
            f"border-bottom:1px solid {C['border_a']}; padding-bottom:6px;")
        root.addWidget(sub)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._contenedor = QWidget()
        self._lay = QVBoxLayout(self._contenedor)
        self._lay.setContentsMargins(0, 0, 6, 0)
        self._lay.setSpacing(10)
        self._scroll.setWidget(self._contenedor)
        root.addWidget(self._scroll)

        self._mostrar_vacio()

    def _limpiar(self):
        while self._lay.count():
            item = self._lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _mostrar_vacio(self):
        lbl = QLabel("Configure y presione  ▶ Resolver")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(
            f"color:{C['text_m']}; font-size:12px; letter-spacing:2px; padding:60px 0;")
        self._lay.addWidget(lbl)

    def _sec_title(self, txt: str) -> QLabel:
        lbl = QLabel(txt.upper())
        lbl.setStyleSheet(
            f"color:{C['accent']}; font-size:9px; font-weight:bold; letter-spacing:3px;"
            f"border-left:2px solid {C['accent']}; padding-left:7px; margin-top:6px;")
        return lbl

    def _make_table(self, headers_h, headers_v, cells,
                    path=None, opt_cell=None) -> QTableWidget:
        rows, cols = len(headers_v), len(headers_h)
        tbl = QTableWidget(rows, cols)
        tbl.setHorizontalHeaderLabels(headers_h)
        tbl.setVerticalHeaderLabels(headers_v)
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        tbl.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

        for r in range(rows):
            for c in range(cols):
                val = cells[r][c] if isinstance(cells[0], list) else cells[c]
                txt = str(val) if val is not None else "∞"
                item = QTableWidgetItem(txt)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)

                key = (r, c) if isinstance(cells[0], list) else c
                if opt_cell and key == opt_cell:
                    item.setForeground(QColor(C["accent3"]))
                    item.setFont(QFont("Courier New", 10, QFont.Weight.Bold))
                elif path and key in path:
                    item.setBackground(QColor(0, 170, 255, 22))
                    item.setForeground(QColor(C["accent"]))
                else:
                    item.setForeground(QColor(C["text_s"]))

                tbl.setItem(r, c, item)

        tbl.setFixedHeight(min(rows * 26 + 34, 320))
        return tbl

    def mostrar_error(self, msg: str):
        self._limpiar()
        self._lbl_hdr.setText("Error")
        lbl = QLabel(f"⚠  {msg}")
        lbl.setWordWrap(True)
        lbl.setStyleSheet(
            f"color:{C['accent4']}; background:{C['bg_card']};"
            f"border:1px solid rgba(255,107,107,80); border-radius:4px;"
            f"padding:10px 14px; font-family:'Courier New',monospace; font-size:11px;")
        self._lay.addWidget(lbl)
        self._lay.addStretch()

    def limpiar_pantalla(self):
        self._limpiar()
        self._lbl_hdr.setText("Sin resultados")
        self._mostrar_vacio()

    def mostrar_resultado(self, d: dict):
        self._limpiar()
        self._lbl_hdr.setText("Resultados")
        lay = self._lay

        lay.addWidget(self._build_info_box(d))
        lay.addWidget(self._build_opt_card(d))
        lay.addWidget(self._sec_title("Tabla DP  f[etapa][recurso disponible s]"))
        lay.addWidget(self._build_dp_table(d))

        if d.get("pasos"):
            lay.addWidget(self._sec_title("Traza de decisiones"))
            lay.addWidget(self._build_pasos(d["pasos"]))

        det = self._build_detalle(d)
        if det:
            lay.addWidget(self._sec_title("Detalle de la solución"))
            lay.addWidget(det)

        lay.addStretch()

    def _build_info_box(self, d: dict) -> QFrame:
        frame = QFrame(); frame.setObjectName("card_info")
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(12, 9, 12, 9)
        lay.setSpacing(5)

        tipo_str = "Maximizar" if d["tipo"] == "max" else "Minimizar"
        t = QLabel(f"<b style='color:{C['accent2']}'>{d['algoritmo']}</b>"
                   f"  —  <span style='color:{C['text_s']}'>{tipo_str}</span>")
        t.setStyleSheet("font-size:12px;")
        lay.addWidget(t)

        rec = QLabel(d.get("recurrencia", ""))
        rec.setStyleSheet(
            f"color:{C['accent']}; background:{C['bg_input']};"
            f"border-radius:3px; padding:4px 8px;"
            f"font-family:'Courier New',monospace; font-size:11px;")
        lay.addWidget(rec)

        if d.get("min_x"):
            mins = d["min_x"]
            filas = d.get("filas", [f"E{i+1}" for i in range(len(mins))])
            txt = "  |  ".join(f"{filas[i]}: min={mins[i]}" for i in range(len(mins)))
            lm = QLabel(f"Restricciones mínimas:  {txt}")
            lm.setStyleSheet(
                f"color:{C['accent2']}; background:{C['bg_input']};"
                f"border-radius:3px; padding:3px 8px;"
                f"font-family:'Courier New',monospace; font-size:10px;")
            lay.addWidget(lm)

        return frame

    def _build_opt_card(self, d: dict) -> QFrame:
        frame = QFrame(); frame.setObjectName("card")
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(28)

        col1 = QVBoxLayout()
        l1 = QLabel("TOTAL ÓPTIMO")
        l1.setStyleSheet(f"color:{C['text_s']}; font-size:9px; letter-spacing:2px;")
        v1 = QLabel(str(d["optimo"]) if d["optimo"] is not None else "∞")
        v1.setStyleSheet(
            f"color:{C['accent3']}; font-size:26px; font-family:'Courier New',monospace;")
        col1.addWidget(l1); col1.addWidget(v1)
        lay.addLayout(col1)

        col2 = QVBoxLayout(); col2.setSpacing(3)

        if "asignaciones" in d and d.get("asignaciones") is not None:
            filas = d.get("filas", [])
            asig  = d["asignaciones"]
            rets  = d.get("retornos", [])
            partes = []
            for i in range(len(asig)):
                nombre = filas[i] if i < len(filas) else f"E{i+1}"
                ret    = rets[i] if i < len(rets) else "?"
                partes.append(f"{nombre}: x={asig[i]} → {ret}")
            col2.addWidget(self._kv("ASIGNACIÓN POR ETAPA", "\n".join(partes), wrap=True))

        elif "seleccionados" in d:
            vals, pesos = d.get("valores", []), d.get("pesos", [])
            items_str = ", ".join(
                f"I{i+1}(v={vals[i]},p={pesos[i]})" for i in d["seleccionados"]
            ) or "(ninguno)"
            col2.addWidget(self._kv("ÍTEMS SELECCIONADOS", items_str, wrap=True))
            col2.addWidget(self._kv("PESO USADO",
                                    f"{d.get('peso_usado',0)} / {d.get('capacidad',0)}"))

        elif "usados" in d:
            vals = d.get("valores", [])
            items_str = ", ".join(
                f"I{int(k)+1}×{v}" for k, v in d["usados"].items()
            ) or "(ninguno)"
            col2.addWidget(self._kv("COMBINACIÓN", items_str, wrap=True))

        elif "camino" in d and d.get("camino"):
            col2.addWidget(self._kv("CAMINO", " → ".join(str(x) for x in d["camino"])))

        lay.addLayout(col2)
        lay.addStretch()

        factible = d.get("factible", False)
        badge = QLabel("ÓPTIMO" if factible else "NO FACTIBLE")
        badge.setStyleSheet(
            f"color:{C['accent3'] if factible else C['accent4']};"
            f"background:{'rgba(0,230,118,30)' if factible else 'rgba(255,107,107,30)'};"
            f"border:1px solid {'rgba(0,230,118,60)' if factible else 'rgba(255,107,107,60)'};"
            f"border-radius:2px; padding:2px 10px; font-size:10px; letter-spacing:1px;")
        lay.addWidget(badge, alignment=Qt.AlignmentFlag.AlignTop)
        return frame

    def _kv(self, key: str, val: str, wrap=False) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(2)
        lk = QLabel(key)
        lk.setStyleSheet(f"color:{C['text_s']}; font-size:9px; letter-spacing:2px;")
        lv = QLabel(val)
        lv.setStyleSheet(
            f"color:{C['text_p']}; font-family:'Courier New',monospace; font-size:11px;")
        if wrap:
            lv.setWordWrap(True)
        lay.addWidget(lk); lay.addWidget(lv)
        return w

    def _build_dp_table(self, d: dict) -> QTableWidget:
        dp  = d["dp"]
        dim = d.get("dim", "2d")
        path = d.get("path", set())

        if dim == "2d":
            opt = (len(dp) - 1, len(dp[0]) - 1)
            return self._make_table(d["columnas"], d["filas"], dp,
                                    path=path, opt_cell=opt)
        else:
            opt = (0, len(dp) - 1)
            path2 = {(0, c) for c in path} if isinstance(next(iter(path), None), int) else path
            return self._make_table(d["columnas"], d["filas"], [dp],
                                    path=path2, opt_cell=opt)

    def _build_pasos(self, pasos: list) -> QTableWidget:
        tbl = QTableWidget(len(pasos), 4)
        tbl.setHorizontalHeaderLabels(["Etapa", "Estado", "Retorno", "Decisión"])
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tbl.verticalHeader().setVisible(False)
        colors = [C["accent2"], C["accent"], C["accent3"], C["text_m"]]
        for r, p in enumerate(pasos):
            for c, (key, col) in enumerate(
                    zip(["etapa", "estado", "valor", "decision"], colors)):
                item = QTableWidgetItem(str(p.get(key, "")))
                item.setForeground(QColor(col))
                item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                tbl.setItem(r, c, item)
        tbl.setFixedHeight(min(len(pasos) * 24 + 34, 220))
        return tbl

    def _build_detalle(self, d: dict):
        """Tabla resumen de asignación con suma acumulada."""
        if "asignaciones" not in d:
            return None

        filas    = d.get("filas", [])
        asig     = d["asignaciones"]
        rets     = d.get("retornos", [])
        min_x    = d.get("min_x", [0] * len(asig))
        demandas = d.get("demandas", [0] * len(asig))

        n = len(asig)
        tbl = QTableWidget(n + 1, 5)
        tbl.setHorizontalHeaderLabels(
            ["Etapa", "x asignado", "Mín requerido", "Retorno", "Σ Acumulado"])
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tbl.verticalHeader().setVisible(False)

        acum = 0
        for r in range(n):
            nombre = filas[r] if r < len(filas) else f"E{r+1}"
            ret    = rets[r] if r < len(rets) else 0
            acum  += ret
            mn     = min_x[r] if r < len(min_x) else 0
            dem    = demandas[r] if r < len(demandas) else mn
            mn_str = f"≥ {dem} ret  (x≥{mn})" if dem > 0 else f"≥ {mn}"
            data = [
                (nombre,          C["accent2"]),
                (str(asig[r]),    C["accent"]),
                (mn_str,          C["text_s"]),
                (str(ret),        C["accent3"]),
                (f"= {acum}",     C["accent3"]),
            ]
            for c, (txt, col) in enumerate(data):
                item = QTableWidgetItem(txt)
                item.setForeground(QColor(col))
                item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                tbl.setItem(r, c, item)

        total_data = [
            ("TOTAL", C["text_s"]),
            (str(sum(asig)), C["accent"]),
            ("", C["text_m"]),
            (str(sum(rets)), C["accent3"]),
            (f"= {sum(rets)}", C["accent3"]),
        ]
        for c, (txt, col) in enumerate(total_data):
            item = QTableWidgetItem(txt)
            item.setForeground(QColor(col))
            item.setFont(QFont("Courier New", 10, QFont.Weight.Bold))
            item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            tbl.setItem(n, c, item)

        tbl.setFixedHeight(min((n + 1) * 24 + 34, 220))
        return tbl

class VentanaPrincipal(QMainWindow):
    """Orquesta Vista y Modelo."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Programación Dinámica — Investigación de Operaciones")
        self.setMinimumSize(1100, 680)
        self.resize(1340, 760)

        self._item_tbl: ItemTableWidget | None = None
        self._mat_wgt:  MatrizWidget    | None = None

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._build_sidebar())
        self._result_panel = PanelResultados()
        splitter.addWidget(self._result_panel)
        splitter.setSizes([300, 1040])
        splitter.setHandleWidth(1)
        root.addWidget(splitter)

        self._generar_campos()

    def _build_header(self) -> QFrame:
        frame = QFrame(); frame.setObjectName("hdr_frame")
        frame.setFixedHeight(16)
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(16, 0, 16, 0)
        lay.setSpacing(10)
        t = QLabel("PROGRAMACIÓN DINÁMICA")
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t.setStyleSheet(
            f"color:{C['accent']}; font-size:11px; font-weight:bold; letter-spacing:4px;")
        return frame

    def _build_sidebar(self) -> QFrame:
        frame = QFrame(); frame.setObjectName("sidebar_frame")
        frame.setFixedWidth(300)

        outer = QVBoxLayout(frame)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner_w = QWidget()
        ilay = QVBoxLayout(inner_w)
        ilay.setContentsMargins(10, 8, 10, 8)
        ilay.setSpacing(8)
        scroll.setWidget(inner_w)
        outer.addWidget(scroll)

        grp_cfg = QGroupBox("Configuración")
        gl = QGridLayout(grp_cfg); gl.setSpacing(7)

        gl.addWidget(QLabel("Tipo:"), 0, 0)
        self._cmb_tipo = QComboBox()
        self._cmb_tipo.addItems(["Maximizar", "Minimizar"])
        gl.addWidget(self._cmb_tipo, 0, 1)

        gl.addWidget(QLabel("Algoritmo:"), 1, 0)
        self._cmb_algo = QComboBox()
        self._cmb_algo.addItems([
            "Mochila 0/1",
            "Mochila Ilimitada",
            "Tabla Personalizada",
            "Camino en DAG",
        ])
        self._cmb_algo.currentIndexChanged.connect(self._on_algo_change)
        gl.addWidget(self._cmb_algo, 1, 1)

        self._lbl_n = QLabel("Nº Ítems / Etapas:")
        gl.addWidget(self._lbl_n, 2, 0)
        self._spn_n = QSpinBox(); self._spn_n.setRange(1, 12); self._spn_n.setValue(3)
        gl.addWidget(self._spn_n, 2, 1)

        self._lbl_w = QLabel("Recurso total (W):")
        gl.addWidget(self._lbl_w, 3, 0)
        self._spn_w = QSpinBox(); self._spn_w.setRange(1, 50); self._spn_w.setValue(10)
        gl.addWidget(self._spn_w, 3, 1)

        btn_gen = QPushButton("Generar campos"); btn_gen.setObjectName("btn_gen")
        btn_gen.clicked.connect(self._generar_campos)
        gl.addWidget(btn_gen, 4, 0, 1, 2)
        ilay.addWidget(grp_cfg)

        self._grp_dat = QGroupBox("Función Objetivo / Datos")
        self._dat_lay = QVBoxLayout(self._grp_dat)
        self._dat_lay.setContentsMargins(8, 10, 8, 8)
        self._dat_lay.setSpacing(6)
        ilay.addWidget(self._grp_dat)

        self._grp_dag = QGroupBox("Parámetros DAG")
        dgl = QGridLayout(self._grp_dag); dgl.setSpacing(6)
        dgl.addWidget(QLabel("Nº Nodos:"), 0, 0)
        self._spn_dag_n = QSpinBox(); self._spn_dag_n.setRange(2, 50); self._spn_dag_n.setValue(5)
        dgl.addWidget(self._spn_dag_n, 0, 1)
        dgl.addWidget(QLabel("Origen:"), 1, 0)
        self._spn_orig = QSpinBox(); self._spn_orig.setRange(0, 49); self._spn_orig.setValue(0)
        dgl.addWidget(self._spn_orig, 1, 1)
        dgl.addWidget(QLabel("Destino:"), 2, 0)
        self._spn_dest = QSpinBox(); self._spn_dest.setRange(0, 49); self._spn_dest.setValue(4)
        dgl.addWidget(self._spn_dest, 2, 1)
        dgl.addWidget(QLabel("Aristas\n(de a peso):"), 3, 0, Qt.AlignmentFlag.AlignTop)
        self._txt_aristas = QTextEdit()
        self._txt_aristas.setPlainText("0 1 5\n0 2 3\n1 3 6\n1 2 2\n2 4 4\n3 4 3\n2 3 1")
        self._txt_aristas.setFixedHeight(110)
        dgl.addWidget(self._txt_aristas, 3, 1)
        ilay.addWidget(self._grp_dag)
        self._grp_dag.setVisible(False)

        ilay.addStretch()

        btn_bar = QWidget()
        btn_bar.setStyleSheet(
            f"background:{C['bg_panel']}; border-top:1px solid {C['border']};")
        blay = QHBoxLayout(btn_bar)
        blay.setContentsMargins(10, 8, 10, 10)
        blay.setSpacing(8)
        btn_clear = QPushButton("↺  Limpiar"); btn_clear.setObjectName("btn_clear")
        btn_clear.clicked.connect(self._limpiar)
        self._btn_solve = QPushButton("▶  Resolver"); self._btn_solve.setObjectName("btn_solve")
        self._btn_solve.clicked.connect(self._resolver)
        blay.addWidget(btn_clear); blay.addWidget(self._btn_solve)
        outer.addWidget(btn_bar)

        return frame

    def _on_algo_change(self):
        idx = self._cmb_algo.currentIndex()
        is_dag = (idx == 3)
        self._lbl_n.setVisible(not is_dag)
        self._spn_n.setVisible(not is_dag)
        self._lbl_w.setVisible(not is_dag)
        self._spn_w.setVisible(not is_dag)
        self._grp_dag.setVisible(is_dag)
        self._generar_campos()

    def _generar_campos(self):
        while self._dat_lay.count():
            item = self._dat_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._item_tbl = None
        self._mat_wgt  = None

        algo = self._cmb_algo.currentIndex()
        n    = self._spn_n.value()
        W    = self._spn_w.value()

        if algo in (0, 1):
            lbl = QLabel("Valor y peso de cada ítem:")
            lbl.setStyleSheet(
                f"color:{C['text_m']}; font-size:9px; font-family:'Courier New';")
            self._dat_lay.addWidget(lbl)
            self._item_tbl = ItemTableWidget(n)
            self._dat_lay.addWidget(self._item_tbl)

        elif algo == 2:
            lbl = QLabel(
                f"r[etapa][x] — {n} etapas, x = 0..{W}\n"
                f"Ingrese el retorno de asignar x unidades a cada etapa.")
            lbl.setStyleSheet(
                f"color:{C['text_m']}; font-size:9px; font-family:'Courier New';")
            lbl.setWordWrap(True)
            self._dat_lay.addWidget(lbl)
            self._mat_wgt = MatrizWidget(n, W)
            self._dat_lay.addWidget(self._mat_wgt)

        else:
            info = QLabel("Configure nodos y aristas\nen el grupo 'Parámetros DAG'.")
            info.setStyleSheet(f"color:{C['text_s']}; font-size:11px;")
            self._dat_lay.addWidget(info)

    def _resolver(self):
        """Lee la Vista → llama al Modelo → actualiza el PanelResultados."""
        tipo = "max" if self._cmb_tipo.currentIndex() == 0 else "min"
        algo = self._cmb_algo.currentIndex()
        W    = self._spn_w.value()

        try:
            if algo == 0:
                if self._item_tbl is None:
                    raise ValueError("Genere los campos primero.")
                vals, pesos, minimos = self._item_tbl.get_data()
                resultado = ModeloPD.mochila_01(vals, pesos, W, tipo, minimos)

            elif algo == 1:
                if self._item_tbl is None:
                    raise ValueError("Genere los campos primero.")
                vals, pesos, minimos = self._item_tbl.get_data()
                resultado = ModeloPD.mochila_ilimitada(vals, pesos, W, tipo, minimos)

            elif algo == 2:
                if self._mat_wgt is None:
                    raise ValueError("Genere los campos primero.")
                matriz, min_x, demandas = self._mat_wgt.get_data(W)
                resultado = ModeloPD.tabla_personalizada(matriz, tipo, min_x)
                if "factible" in resultado and resultado["factible"]:
                    resultado["demandas"] = demandas

            else:
                n_nodos = self._spn_dag_n.value()
                origen  = self._spn_orig.value()
                destino = self._spn_dest.value()
                lineas  = self._txt_aristas.toPlainText().strip().split("\n")
                aristas = []
                for linea in lineas:
                    parts = linea.strip().split()
                    if len(parts) >= 3:
                        try:
                            aristas.append(
                                (int(parts[0]), int(parts[1]), int(parts[2])))
                        except ValueError:
                            pass
                if not aristas:
                    raise ValueError(
                        "Ingrese al menos una arista válida (formato: de a peso).")
                resultado = ModeloPD.camino_dag(
                    n_nodos, aristas, origen, destino, tipo)

            if resultado.get("error"):
                self._result_panel.mostrar_error(resultado["error"])
            else:
                self._result_panel.mostrar_resultado(resultado)

        except Exception as exc:
            self._result_panel.mostrar_error(str(exc))

    def _limpiar(self):
        self._result_panel.limpiar_pantalla()

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Programación Dinámica MVC")
    app.setStyleSheet(QSS)
    app.setFont(QFont("Segoe UI", 11))
    ventana = VentanaPrincipal()
    ventana.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()