from typing import Callable, List, Optional, Protocol, Tuple

from qtpy.QtCore import QObject, QSize, Signal
from qtpy.QtGui import QDoubleValidator, QValidator
from qtpy.QtWidgets import QGridLayout, QLineEdit, QWidget


class DoubleValidator(QDoubleValidator):
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.last_valid: str = "0"

    def fixup(self, text: str) -> str:
        return self.last_valid

    def validate(
        self, text: str, pos: int
    ) -> Tuple[QValidator.State, str, int]:
        state, text, pos = super().validate(text, pos)
        if state == QValidator.State.Acceptable:
            self.last_valid = text
        return state, text, pos


class PositiveDoubleValidator(QDoubleValidator):
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.last_valid: str = "1"

    def fixup(self, text: str) -> str:
        return self.last_valid

    def validate(
        self, text: str, pos: int
    ) -> Tuple[QValidator.State, str, int]:
        state, text, pos = super().validate(text, pos)
        if state == QValidator.State.Acceptable and float(text) <= 0:
            state = QValidator.State.Intermediate
        if state == QValidator.State.Acceptable:
            self.last_valid = text
        return state, text, pos


class MinimalLineEdit(QLineEdit):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.editingFinished.connect(self._moveCursorToStart)

    def _moveCursorToStart(self) -> None:
        self.setCursorPosition(0)

    def sizeHint(self) -> QSize:
        return self.minimumSizeHint()


class DoubleLineEdit(MinimalLineEdit):
    valueChanged = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setValidator(DoubleValidator())
        self.editingFinished.connect(self.valueChanged)

    def setText(self, text: str) -> None:
        self.setValue(float(text))

    def setValue(self, value: float) -> None:
        text = str(value)
        state, text, _ = self.validator().validate(text, 0)
        if state != QValidator.State.Acceptable:
            raise ValueError("Value is invalid.")
        if text != self.text():
            super().setText(text)
            self.editingFinished.emit()

    def value(self) -> float:
        return float(self.text())


class ReadOnlyLineEdit(MinimalLineEdit):
    def __init__(
        self, *, parent: Optional[QWidget] = None, text: Optional[str] = None
    ) -> None:
        super().__init__(parent)
        if text is not None:
            self.setText(text)
        self.setReadOnly(True)
        self.setStyleSheet("QLineEdit{" "background: transparent;" "}")

    def setText(self, text: str) -> None:
        super().setText(text)
        self._moveCursorToStart()


def readonly_lineedit(text: Optional[str] = None) -> ReadOnlyLineEdit:
    return ReadOnlyLineEdit(text=text)


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
