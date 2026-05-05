import sys
import re
from fractions import Fraction
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QSpinBox, QScrollArea,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView, QStackedWidget,
    QTextEdit, QSplitter, QMessageBox, QGridLayout, QGroupBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor, QPalette, QLinearGradient, QGradient, QPainter, QBrush

M_VALUE = 1_000_000


def parse_expr(expr_str, var_names):
    coeffs = {v: Fraction(0) for v in var_names}
    expr_str = expr_str.replace(" ", "").replace("-", "+-")
    terms = expr_str.split("+")
    for term in terms:
        if not term:
            continue
        for v in sorted(var_names, key=len, reverse=True):
            pattern = rf'^([+-]?\d*\.?\d*)\*?{re.escape(v)}$'
            m = re.match(pattern, term)
            if m:
                c = m.group(1)
                if c in ("", "+"):
                    c = "1"
                elif c == "-":
                    c = "-1"
                coeffs[v] = Fraction(c).limit_denominator(1000)
                break
    return coeffs


def parse_constraint(line, var_names):
    for op in [">=", "<=", "="]:
        if op in line:
            parts = line.split(op, 1)
            lhs = parts[0].strip()
            rhs = Fraction(parts[1].strip()).limit_denominator(1000)
            coeffs = parse_expr(lhs, var_names)
            return coeffs, op, rhs
    raise ValueError(f"Restricción inválida: {line}")


def solve_gran_m(maximizar, n_orig, fo_str, constraint_lines):
    orig_vars = [f"x{i+1}" for i in range(n_orig)]
    fo_coeffs = parse_expr(fo_str, orig_vars)

    constraints = []
    for line in constraint_lines:
        c, op, rhs = parse_constraint(line, orig_vars)
        if rhs < 0:
            c = {k: -v for k, v in c.items()}
            rhs = -rhs
            op = ">=" if op == "<=" else ("<=" if op == ">=" else "=")
        constraints.append((c, op, rhs))

    slack_vars, excess_vars, art_vars = [], [], []
    for i, (_, op, _) in enumerate(constraints):
        if op == "<=":
            slack_vars.append(f"s{i+1}")
        elif op == ">=":
            excess_vars.append(f"e{i+1}")
            art_vars.append(f"a{i+1}")
        elif op == "=":
            art_vars.append(f"a{i+1}")

    all_vars = orig_vars + slack_vars + excess_vars + art_vars
    n_vars = len(all_vars)
    n_rows = len(constraints)
    var_idx = {v: j for j, v in enumerate(all_vars)}

    c_j = {}
    for v in orig_vars:
        c_j[v] = fo_coeffs[v] if maximizar else -fo_coeffs[v]
    for v in slack_vars:
        c_j[v] = Fraction(0)
    for v in excess_vars:
        c_j[v] = Fraction(0)
    for v in art_vars:
        c_j[v] = Fraction(-M_VALUE)

    tableau = [[Fraction(0)] * n_vars for _ in range(n_rows)]
    b = [Fraction(0)] * n_rows

    vb, cb = [], []
    s_idx = e_idx = a_idx = 0
    for i, (c, op, rhs) in enumerate(constraints):
        b[i] = rhs
        for v in orig_vars:
            tableau[i][var_idx[v]] = c[v]
        if op == "<=":
            sv = slack_vars[s_idx]; s_idx += 1
            tableau[i][var_idx[sv]] = Fraction(1)
            vb.append(sv); cb.append(Fraction(0))
        elif op == ">=":
            ev = excess_vars[e_idx]; e_idx += 1
            av = art_vars[a_idx]; a_idx += 1
            tableau[i][var_idx[ev]] = Fraction(-1)
            tableau[i][var_idx[av]] = Fraction(1)
            vb.append(av); cb.append(Fraction(-M_VALUE))
        elif op == "=":
            av = art_vars[a_idx]; a_idx += 1
            tableau[i][var_idx[av]] = Fraction(1)
            vb.append(av); cb.append(Fraction(-M_VALUE))

    iterations = []
    max_iter = 100
    iteration = 0
    pivot_info = None

    while iteration < max_iter:
        z_j, cj_zj = [], []
        for j in range(n_vars):
            zj = sum(cb[i] * tableau[i][j] for i in range(n_rows))
            z_j.append(zj)
            cj_zj.append(c_j[all_vars[j]] - zj)

        z_val = sum(cb[i] * b[i] for i in range(n_rows))

        iterations.append({
            "iteration": iteration,
            "all_vars": list(all_vars),
            "vb": list(vb),
            "cb": list(cb),
            "c_j": dict(c_j),
            "tableau": [list(row) for row in tableau],
            "b": list(b),
            "z_j": list(z_j),
            "cj_zj": list(cj_zj),
            "z_val": z_val,
            "pivot_info": pivot_info,
        })

        best_czj = max(cj_zj)
        if best_czj <= 1e-9:
            break

        pivot_col = cj_zj.index(best_czj)
        min_ratio = None
        pivot_row = -1
        for i in range(n_rows):
            if tableau[i][pivot_col] > 1e-12:
                ratio = b[i] / tableau[i][pivot_col]
                if min_ratio is None or ratio < min_ratio:
                    min_ratio = ratio
                    pivot_row = i

        if pivot_row == -1:
            return iterations, {"status": "unbounded"}

        entering = all_vars[pivot_col]
        leaving = vb[pivot_row]
        pivot_info = {"entering": entering, "leaving": leaving, "row": pivot_row, "col": pivot_col}

        pivot_val = tableau[pivot_row][pivot_col]
        tableau[pivot_row] = [x / pivot_val for x in tableau[pivot_row]]
        b[pivot_row] /= pivot_val
        for i in range(n_rows):
            if i != pivot_row:
                factor = tableau[i][pivot_col]
                tableau[i] = [tableau[i][j] - factor * tableau[pivot_row][j] for j in range(n_vars)]
                b[i] -= factor * b[pivot_row]

        vb[pivot_row] = entering
        cb[pivot_row] = c_j[entering]
        iteration += 1
    else:
        return iterations, {"status": "max_iter"}

    # Check feasibility
    for v, bval in zip(vb, b):
        if v in art_vars and abs(float(bval)) > 1e-6:
            return iterations, {"status": "infeasible"}

    sol = {v: Fraction(0) for v in orig_vars}
    for i, v in enumerate(vb):
        if v in orig_vars:
            sol[v] = b[i]

    z_opt = sum(c_j[vb[i]] * b[i] for i in range(n_rows))
    z_real = z_opt if maximizar else -z_opt

    slack_sol = {}
    for v in slack_vars + excess_vars:
        slack_sol[v] = Fraction(0)
        for i, bv in enumerate(vb):
            if bv == v:
                slack_sol[v] = b[i]
                break

    return iterations, {
        "status": "optimal",
        "sol": sol,
        "z_real": z_real,
        "slack_sol": slack_sol,
        "orig_vars": orig_vars,
        "maximizar": maximizar,
    }


DARK_BG     = "#0D1117"
PANEL_BG    = "#161B22"
CARD_BG     = "#1C2128"
BORDER      = "#30363D"
ACCENT      = "#58A6FF"
ACCENT2     = "#3FB950"
WARN        = "#F78166"
TEXT_MAIN   = "#E6EDF3"
TEXT_DIM    = "#8B949E"
TEXT_GOLD   = "#E3B341"
PIVOT_COL   = "#1F3A5F"
PIVOT_ROW   = "#1F3A2F"
PIVOT_CELL  = "#2D5A1B"
HEADER_BG   = "#21262D"

MONO = QFont("Courier New", 10)
MONO.setStyleHint(QFont.StyleHint.Monospace)


def fmt_frac(val):
    if isinstance(val, Fraction):
        if val.denominator == 1:
            return str(val.numerator)
        f = float(val)
        return f"{f:.4f}".rstrip('0').rstrip('.')
    if isinstance(val, (int, float)):
        if abs(val) > 900_000:
            return "+M" if val > 0 else "-M"
        if val == int(val):
            return str(int(val))
        return f"{val:.4f}".rstrip('0').rstrip('.')
    return str(val)


def styled_item(text, bg=None, fg=TEXT_MAIN, bold=False, center=True):
    item = QTableWidgetItem(str(text))
    if center:
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
    if bg:
        item.setBackground(QColor(bg))
    item.setForeground(QColor(fg))
    if bold:
        f = item.font()
        f.setBold(True)
        item.setFont(f)
    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
    return item

STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {DARK_BG};
    color: {TEXT_MAIN};
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
    font-size: 13px;
}}

QGroupBox {{
    border: 1px solid {BORDER};
    border-radius: 8px;
    margin-top: 14px;
    padding: 10px;
    background-color: {PANEL_BG};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: {ACCENT};
    font-weight: bold;
    font-size: 12px;
    letter-spacing: 1px;
}}

QLabel {{
    color: {TEXT_MAIN};
}}

QLineEdit, QSpinBox, QComboBox {{
    background-color: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 6px 10px;
    color: {TEXT_MAIN};
    font-size: 13px;
    selection-background-color: {ACCENT};
}}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
    border-color: {ACCENT};
}}
QComboBox::drop-down {{
    border: none;
    padding-right: 8px;
}}
QComboBox QAbstractItemView {{
    background-color: {CARD_BG};
    selection-background-color: {ACCENT};
    color: {TEXT_MAIN};
    border: 1px solid {BORDER};
}}
QSpinBox::up-button, QSpinBox::down-button {{
    background-color: {BORDER};
    border-radius: 3px;
    width: 18px;
}}

QPushButton {{
    background-color: {ACCENT};
    color: #0D1117;
    border: none;
    border-radius: 7px;
    padding: 9px 20px;
    font-weight: bold;
    font-size: 13px;
    letter-spacing: 0.5px;
}}
QPushButton:hover {{
    background-color: #79BBFF;
}}
QPushButton:pressed {{
    background-color: #3A7BD5;
}}
QPushButton#btnSecondary {{
    background-color: {CARD_BG};
    color: {TEXT_MAIN};
    border: 1px solid {BORDER};
}}
QPushButton#btnSecondary:hover {{
    border-color: {ACCENT};
    color: {ACCENT};
}}
QPushButton#btnSuccess {{
    background-color: {ACCENT2};
    color: #0D1117;
}}
QPushButton#btnSuccess:hover {{
    background-color: #56D364;
}}
QPushButton#btnDanger {{
    background-color: {WARN};
    color: #0D1117;
}}

QTableWidget {{
    background-color: {CARD_BG};
    gridline-color: {BORDER};
    border: 1px solid {BORDER};
    border-radius: 6px;
    color: {TEXT_MAIN};
    font-family: 'Courier New', monospace;
    font-size: 12px;
}}
QTableWidget::item {{
    padding: 5px 8px;
}}
QTableWidget::item:selected {{
    background-color: #1F3A5F;
}}
QHeaderView::section {{
    background-color: {HEADER_BG};
    color: {ACCENT};
    padding: 6px;
    border: none;
    border-bottom: 1px solid {BORDER};
    font-weight: bold;
    font-size: 11px;
    letter-spacing: 0.5px;
}}

QScrollArea {{
    border: none;
    background-color: transparent;
}}
QScrollBar:vertical {{
    background-color: {PANEL_BG};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background-color: {BORDER};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background-color: {ACCENT};
}}
QScrollBar:horizontal {{
    background-color: {PANEL_BG};
    height: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:horizontal {{
    background-color: {BORDER};
    border-radius: 4px;
}}
QScrollBar::add-line, QScrollBar::sub-line {{
    width: 0; height: 0;
}}

QTextEdit {{
    background-color: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 6px;
    color: {TEXT_MAIN};
    font-family: 'Courier New', monospace;
    font-size: 12px;
    padding: 8px;
}}

QSplitter::handle {{
    background-color: {BORDER};
}}
"""

class InputPanel(QWidget):
    solve_requested = pyqtSignal(bool, int, str, list)

    def __init__(self):
        super().__init__()
        self._constraint_rows = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title = QLabel("MÉTODO DE LA GRAN M")
        title.setFont(QFont("Courier New", 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {ACCENT}; letter-spacing: 3px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        sub = QLabel("Investigación de Operaciones")
        sub.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; letter-spacing: 2px;")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sub)

        # Objective type + vars + constraints count
        config_group = QGroupBox("CONFIGURACIÓN")
        config_layout = QGridLayout(config_group)
        config_layout.setSpacing(10)

        config_layout.addWidget(QLabel("Tipo:"), 0, 0)
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["Maximizar", "Minimizar"])
        config_layout.addWidget(self.combo_tipo, 0, 1)

        config_layout.addWidget(QLabel("Variables de decisión:"), 1, 0)
        self.spin_vars = QSpinBox()
        self.spin_vars.setRange(1, 10)
        self.spin_vars.setValue(2)
        config_layout.addWidget(self.spin_vars, 1, 1)

        config_layout.addWidget(QLabel("Nº de restricciones:"), 2, 0)
        self.spin_constr = QSpinBox()
        self.spin_constr.setRange(1, 10)
        self.spin_constr.setValue(2)
        config_layout.addWidget(self.spin_constr, 2, 1)

        btn_generate = QPushButton("Generar campos")
        btn_generate.setObjectName("btnSecondary")
        btn_generate.clicked.connect(self._generate_fields)
        config_layout.addWidget(btn_generate, 3, 0, 1, 2)

        layout.addWidget(config_group)

        # Objective function
        self.fo_group = QGroupBox("FUNCIÓN OBJETIVO")
        fo_layout = QVBoxLayout(self.fo_group)
        self.fo_hint = QLabel("Ejemplo: 5x1 + 4x2 + 3x3")
        self.fo_hint.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px;")
        fo_layout.addWidget(self.fo_hint)
        self.fo_input = QLineEdit()
        self.fo_input.setPlaceholderText("5x1 + 4x2")
        fo_layout.addWidget(self.fo_input)
        layout.addWidget(self.fo_group)

        # Constraints
        self.constr_group = QGroupBox("RESTRICCIONES")
        self.constr_layout = QVBoxLayout(self.constr_group)
        hint = QLabel("Ejemplo: 6x1 + 3x2 <= 96   |   Operadores: <=  >=  =")
        hint.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px;")
        self.constr_layout.addWidget(hint)
        layout.addWidget(self.constr_group)

        # Buttons
        btn_row = QHBoxLayout()
        self.btn_solve = QPushButton("▶  RESOLVER")
        self.btn_solve.setObjectName("btnSuccess")
        self.btn_solve.clicked.connect(self._on_solve)
        self.btn_clear = QPushButton("↺  Limpiar")
        self.btn_clear.setObjectName("btnSecondary")
        self.btn_clear.clicked.connect(self._clear)
        btn_row.addWidget(self.btn_clear)
        btn_row.addWidget(self.btn_solve)
        layout.addLayout(btn_row)

        layout.addStretch()

        # Auto-generate default fields
        self._generate_fields()

    def _generate_fields(self):
        n = self.spin_vars.value()
        m = self.spin_constr.value()

        # Update FO hint
        self.fo_hint.setText("Ejemplo: " + " + ".join(f"?x{i+1}" for i in range(n)))
        self.fo_input.setPlaceholderText(" + ".join(f"?x{i+1}" for i in range(n)))

        # Remove old constraint rows
        for row_widget in self._constraint_rows:
            self.constr_layout.removeWidget(row_widget)
            row_widget.deleteLater()
        self._constraint_rows.clear()

        for i in range(m):
            row_w = QWidget()
            row_l = QHBoxLayout(row_w)
            row_l.setContentsMargins(0, 0, 0, 0)
            row_l.setSpacing(6)

            lbl = QLabel(f"R{i+1}:")
            lbl.setStyleSheet(f"color: {TEXT_GOLD}; font-weight: bold; min-width: 24px;")
            row_l.addWidget(lbl)

            inp = QLineEdit()
            inp.setPlaceholderText(f"ej. 2x1 + 3x2 <= 10")
            row_l.addWidget(inp)

            self.constr_layout.addWidget(row_w)
            self._constraint_rows.append(row_w)
            row_w.input = inp

    def _on_solve(self):
        n = self.spin_vars.value()
        maximizar = self.combo_tipo.currentIndex() == 0
        fo_str = self.fo_input.text().strip()
        if not fo_str:
            QMessageBox.warning(self, "Error", "Ingrese la función objetivo.")
            return

        constraint_lines = []
        for rw in self._constraint_rows:
            txt = rw.input.text().strip()
            if not txt:
                QMessageBox.warning(self, "Error", "Complete todas las restricciones.")
                return
            constraint_lines.append(txt)

        self.solve_requested.emit(maximizar, n, fo_str, constraint_lines)

    def _clear(self):
        self.fo_input.clear()
        for rw in self._constraint_rows:
            rw.input.clear()

class IterationTable(QWidget):
    def __init__(self, data):
        super().__init__()
        self._build(data)

    def _build(self, data):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(0, 0, 0, 0)

        it = data["iteration"]
        pivot = data.get("pivot_info")
        all_vars = data["all_vars"]
        vb = data["vb"]
        cb = data["cb"]
        c_j = data["c_j"]
        tableau = data["tableau"]
        b = data["b"]
        z_j = data["z_j"]
        cj_zj = data["cj_zj"]
        z_val = data["z_val"]

        n_vars = len(all_vars)
        n_rows = len(vb)

        # Header label
        hdr = QLabel(f"  ITERACIÓN {it}")
        hdr.setStyleSheet(
            f"background-color: {HEADER_BG}; color: {ACCENT}; "
            f"font-family: 'Courier New'; font-weight: bold; font-size: 13px; "
            f"padding: 6px 12px; border-radius: 6px 6px 0 0; letter-spacing: 1px;"
        )
        layout.addWidget(hdr)

        if pivot:
            info = QLabel(
                f"  ↳  Entra: {pivot['entering']}   |   Sale: {pivot['leaving']}"
            )
            info.setStyleSheet(
                f"color: {ACCENT2}; font-family: 'Courier New'; "
                f"font-size: 11px; padding: 3px 12px;"
            )
            layout.addWidget(info)

        # Table: rows = Cj, VB rows, Zj, Cj-Zj  |  cols = VB, CB, vars..., bj
        n_table_cols = 2 + n_vars + 1   # VB, CB, vars, bj
        n_table_rows = 2 + n_rows + 2   # Cj header, sep, body rows, Zj, Cj-Zj

        tbl = QTableWidget(n_table_rows, n_table_cols)
        tbl.setFont(MONO)
        tbl.horizontalHeader().setVisible(False)
        tbl.verticalHeader().setVisible(False)
        tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tbl.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        tbl.setShowGrid(True)
        tbl.setAlternatingRowColors(False)

        # Col headers row 0: blank, blank, var names, bj
        tbl.setItem(0, 0, styled_item("", bg=HEADER_BG, fg=ACCENT, bold=True))
        tbl.setItem(0, 1, styled_item("", bg=HEADER_BG, fg=ACCENT, bold=True))
        for j, v in enumerate(all_vars):
            tbl.setItem(0, 2 + j, styled_item(v, bg=HEADER_BG, fg=ACCENT, bold=True))
        tbl.setItem(0, 2 + n_vars, styled_item("bj", bg=HEADER_BG, fg=TEXT_GOLD, bold=True))

        # Row 1: Cj values
        tbl.setItem(1, 0, styled_item("Cj", bg=HEADER_BG, fg=TEXT_DIM, bold=True))
        tbl.setItem(1, 1, styled_item("", bg=HEADER_BG))
        for j, v in enumerate(all_vars):
            val = c_j[v]
            is_art = v.startswith("a")
            col_bg = "#2D1B1B" if is_art else HEADER_BG
            fg = WARN if is_art else TEXT_GOLD
            tbl.setItem(1, 2 + j, styled_item(fmt_frac(val), bg=col_bg, fg=fg, bold=True))
        tbl.setItem(1, 2 + n_vars, styled_item("", bg=HEADER_BG))

        # Col header row separator: VB / CB labels
        tbl.setItem(2, 0, styled_item("VB", bg=HEADER_BG, fg=ACCENT, bold=True))
        tbl.setItem(2, 1, styled_item("CB", bg=HEADER_BG, fg=ACCENT, bold=True))
        for j in range(n_vars):
            tbl.setItem(2, 2 + j, styled_item("", bg=HEADER_BG))
        tbl.setItem(2, 2 + n_vars, styled_item("", bg=HEADER_BG))

        # Body rows
        pivot_col = pivot["col"] if pivot else -1
        pivot_row_idx = pivot["row"] if pivot else -1

        for i in range(n_rows):
            row_idx = 3 + i
            row_bg = PIVOT_ROW if i == pivot_row_idx else None

            tbl.setItem(row_idx, 0, styled_item(vb[i], bg=row_bg or CARD_BG, fg=ACCENT2 if i == pivot_row_idx else TEXT_MAIN, bold=i == pivot_row_idx))
            tbl.setItem(row_idx, 1, styled_item(fmt_frac(cb[i]), bg=row_bg or CARD_BG, fg=TEXT_GOLD))

            for j in range(n_vars):
                cell_bg = PIVOT_CELL if (i == pivot_row_idx and j == pivot_col) else \
                          PIVOT_COL if j == pivot_col else \
                          (row_bg or CARD_BG)
                val = tableau[i][j]
                tbl.setItem(row_idx, 2 + j, styled_item(fmt_frac(val), bg=cell_bg))

            # bj column
            tbl.setItem(row_idx, 2 + n_vars, styled_item(fmt_frac(b[i]), bg=row_bg or CARD_BG, fg=TEXT_MAIN, bold=True))

        # Zj row
        zj_row = 3 + n_rows
        tbl.setItem(zj_row, 0, styled_item("Zj", bg=HEADER_BG, fg=TEXT_DIM, bold=True))
        tbl.setItem(zj_row, 1, styled_item("", bg=HEADER_BG))
        for j in range(n_vars):
            bg = PIVOT_COL if j == pivot_col else HEADER_BG
            tbl.setItem(zj_row, 2 + j, styled_item(fmt_frac(z_j[j]), bg=bg, fg=TEXT_DIM))
        tbl.setItem(zj_row, 2 + n_vars, styled_item(fmt_frac(z_val), bg=HEADER_BG, fg=TEXT_GOLD, bold=True))

        # Cj-Zj row
        czj_row = 3 + n_rows + 1
        tbl.setItem(czj_row, 0, styled_item("Cj-Zj", bg=HEADER_BG, fg=WARN, bold=True))
        tbl.setItem(czj_row, 1, styled_item("", bg=HEADER_BG))
        for j in range(n_vars):
            val = cj_zj[j]
            # Highlight the pivot column (entering variable)
            is_best = (j == pivot_col)
            bg = PIVOT_COL if is_best else HEADER_BG
            fg = ACCENT2 if is_best else (WARN if float(val) > 1e-9 else TEXT_DIM)
            tbl.setItem(czj_row, 2 + j, styled_item(fmt_frac(val), bg=bg, fg=fg, bold=is_best))
        tbl.setItem(czj_row, 2 + n_vars, styled_item("", bg=HEADER_BG))

        # Resize
        tbl.resizeColumnsToContents()
        tbl.resizeRowsToContents()

        # Fixed height
        total_h = sum(tbl.rowHeight(r) for r in range(n_table_rows)) + 30
        tbl.setFixedHeight(min(total_h, 400))

        layout.addWidget(tbl)

class ResultsPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        top_bar = QHBoxLayout()
        self.status_label = QLabel("Sin resultados")
        self.status_label.setFont(QFont("Courier New", 14, QFont.Weight.Bold))
        self.status_label.setStyleSheet(f"color: {TEXT_DIM};")
        top_bar.addWidget(self.status_label)
        top_bar.addStretch()
        layout.addLayout(top_bar)

        # Result summary card
        self.summary_frame = QFrame()
        self.summary_frame.setStyleSheet(
            f"background-color: {PANEL_BG}; border: 1px solid {BORDER}; "
            f"border-radius: 8px; padding: 10px;"
        )
        self.summary_layout = QVBoxLayout(self.summary_frame)
        layout.addWidget(self.summary_frame)
        self.summary_frame.setVisible(False)

        # Iterations scroll area
        iter_label = QLabel("TABLAS SIMPLEX")
        iter_label.setStyleSheet(f"color: {ACCENT}; font-weight: bold; letter-spacing: 2px; font-size: 11px;")
        layout.addWidget(iter_label)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_inner = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_inner)
        self.scroll_layout.setSpacing(16)
        self.scroll_layout.setContentsMargins(4, 4, 4, 4)
        self.scroll_layout.addStretch()
        self.scroll.setWidget(self.scroll_inner)
        layout.addWidget(self.scroll, stretch=1)

    def clear(self):
        # Remove all iteration tables
        while self.scroll_layout.count() > 1:
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.summary_frame.setVisible(False)
        self.status_label.setText("Calculando...")
        self.status_label.setStyleSheet(f"color: {TEXT_DIM};")

    def show_results(self, iterations, result):
        self.clear()

        # Add iteration tables
        for data in iterations:
            tbl_widget = IterationTable(data)
            self.scroll_layout.insertWidget(self.scroll_layout.count() - 1, tbl_widget)

        # Summary
        status = result["status"]

        # Clear old summary widgets
        while self.summary_layout.count():
            item = self.summary_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.summary_frame.setVisible(True)

        if status == "optimal":
            self.status_label.setText("✓  SOLUCIÓN ÓPTIMA ENCONTRADA")
            self.status_label.setStyleSheet(f"color: {ACCENT2}; font-weight: bold;")

            # Z value
            z_real = result["z_real"]
            tipo_str = "MÁXIMO" if result["maximizar"] else "MÍNIMO"
            z_lbl = QLabel(f"Z* = {fmt_frac(z_real)}   ({tipo_str})")
            z_lbl.setFont(QFont("Courier New", 16, QFont.Weight.Bold))
            z_lbl.setStyleSheet(f"color: {TEXT_GOLD}; padding: 8px 0;")
            self.summary_layout.addWidget(z_lbl)

            # Decision vars
            dvars_lbl = QLabel("Variables de decisión:")
            dvars_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; font-weight: bold; letter-spacing: 1px; margin-top: 6px;")
            self.summary_layout.addWidget(dvars_lbl)

            for v in result["orig_vars"]:
                val = result["sol"][v]
                row = QHBoxLayout()
                vl = QLabel(f"  {v}")
                vl.setFont(QFont("Courier New", 13, QFont.Weight.Bold))
                vl.setStyleSheet(f"color: {ACCENT}; min-width: 40px;")
                eq = QLabel("=")
                eq.setStyleSheet(f"color: {TEXT_DIM};")
                vv = QLabel(fmt_frac(val))
                vv.setFont(QFont("Courier New", 13, QFont.Weight.Bold))
                vv.setStyleSheet(f"color: {TEXT_MAIN};")
                row.addWidget(vl)
                row.addWidget(eq)
                row.addWidget(vv)
                row.addStretch()
                self.summary_layout.addLayout(row)

            # Slack/surplus
            slack_sol = result.get("slack_sol", {})
            if slack_sol:
                sl_lbl = QLabel("Holguras / Excesos:")
                sl_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; font-weight: bold; letter-spacing: 1px; margin-top: 8px;")
                self.summary_layout.addWidget(sl_lbl)
                for v, val in slack_sol.items():
                    row = QHBoxLayout()
                    vl = QLabel(f"  {v}")
                    vl.setFont(QFont("Courier New", 12))
                    vl.setStyleSheet(f"color: {TEXT_DIM}; min-width: 40px;")
                    eq = QLabel("=")
                    eq.setStyleSheet(f"color: {TEXT_DIM};")
                    vv = QLabel(fmt_frac(val))
                    vv.setFont(QFont("Courier New", 12))
                    vv.setStyleSheet(f"color: {TEXT_DIM};")
                    row.addWidget(vl); row.addWidget(eq); row.addWidget(vv); row.addStretch()
                    self.summary_layout.addLayout(row)

        elif status == "infeasible":
            self.status_label.setText("✗  PROBLEMA INFACTIBLE")
            self.status_label.setStyleSheet(f"color: {WARN}; font-weight: bold;")
            msg = QLabel("Una variable artificial permanece en la base con valor > 0.\nNo existe solución factible.")
            msg.setStyleSheet(f"color: {WARN}; font-family: 'Courier New'; padding: 8px;")
            self.summary_layout.addWidget(msg)

        elif status == "unbounded":
            self.status_label.setText("⚠  PROBLEMA NO ACOTADO")
            self.status_label.setStyleSheet(f"color: {TEXT_GOLD}; font-weight: bold;")
            msg = QLabel("No existe solución óptima finita.")
            msg.setStyleSheet(f"color: {TEXT_GOLD}; font-family: 'Courier New'; padding: 8px;")
            self.summary_layout.addWidget(msg)

        elif status == "max_iter":
            self.status_label.setText("⚠  LÍMITE DE ITERACIONES")
            self.status_label.setStyleSheet(f"color: {TEXT_GOLD}; font-weight: bold;")
            msg = QLabel("Se alcanzó el máximo de iteraciones sin convergencia.")
            msg.setStyleSheet(f"color: {TEXT_GOLD}; font-family: 'Courier New'; padding: 8px;")
            self.summary_layout.addWidget(msg)

        # Scroll to bottom (last iteration)
        QTimer.singleShot(100, lambda: self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()
        ))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Método de la Gran M — Investigación de Operaciones")
        self.resize(1200, 800)
        self.setMinimumSize(900, 600)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left panel (input) - fixed width
        self.input_panel = InputPanel()
        self.input_panel.setFixedWidth(340)
        self.input_panel.setStyleSheet(f"background-color: {PANEL_BG};")
        self.input_panel.solve_requested.connect(self._on_solve)

        # Separator line
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet(f"color: {BORDER};")

        # Right panel (results) - expandable
        self.results_panel = ResultsPanel()

        main_layout.addWidget(self.input_panel)
        main_layout.addWidget(sep)
        main_layout.addWidget(self.results_panel, stretch=1)

    def _on_solve(self, maximizar, n_orig, fo_str, constraint_lines):
        self.results_panel.clear()
        try:
            iterations, result = solve_gran_m(maximizar, n_orig, fo_str, constraint_lines)
            self.results_panel.show_results(iterations, result)
        except Exception as e:
            QMessageBox.critical(self, "Error al resolver", str(e))
            self.results_panel.status_label.setText("Error al resolver")
            self.results_panel.status_label.setStyleSheet(f"color: {WARN};")

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()