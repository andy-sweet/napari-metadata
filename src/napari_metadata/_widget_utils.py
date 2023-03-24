from typing import Callable, List, Optional, Protocol, Tuple

from qtpy.QtCore import QObject, Signal
from qtpy.QtGui import QDoubleValidator, QValidator
from qtpy.QtWidgets import QGridLayout, QLineEdit, QWidget


class PositiveDoubleValidator(QDoubleValidator):
    MIN_VALUE: float = 1e-6

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.setBottom(self.MIN_VALUE)

    def fixup(self, text: str) -> str:
        try:
            value = float(text)
            if value < self.MIN_VALUE:
                return str(self.MIN_VALUE)
        except ValueError:
            # Ignore cast errors and just return the input.
            pass
        return text


class DoubleLineEdit(QLineEdit):
    valueChanged = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setValidator(QDoubleValidator())
        self.editingFinished.connect(self.valueChanged)

    def setValue(self, value: float) -> None:
        text = str(value)
        state, text, _ = self.validator().validate(text, 0)
        if state != QValidator.State.Acceptable:
            raise ValueError("Value must be a positive real number.")
        if text != self.text():
            self.setText(text)
            self.editingFinished.emit()

    def value(self) -> float:
        return float(self.text())


def readonly_lineedit(text: Optional[str] = None) -> QLineEdit:
    widget = QLineEdit()
    if text is not None:
        widget.setText(text)
    widget.setReadOnly(True)
    widget.setStyleSheet("QLineEdit{" "background: transparent;" "}")
    return widget


class GridRow(Protocol):
    def widgets() -> Tuple[QWidget, ...]:
        ...


def set_row_visible(row: GridRow, visible: bool) -> None:
    for w in row.widgets():
        w.setVisible(visible)


def update_num_rows(
    *,
    rows: List[GridRow],
    layout: QGridLayout,
    desired_num: int,
    row_factory: Callable[[], GridRow]
) -> None:
    current_num = len(rows)
    # Add any missing widgets.
    for _ in range(desired_num - current_num):
        row = row_factory()
        index = layout.count()
        for col, w in enumerate(row.widgets()):
            layout.addWidget(w, index, col)
        rows.append(row)
    # Remove any unneeded widgets.
    for _ in range(current_num - 1, desired_num - 1, -1):
        row = rows.pop()
        for w in row.widgets():
            layout.removeWidget(w)
