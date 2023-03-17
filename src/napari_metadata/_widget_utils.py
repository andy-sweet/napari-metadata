from typing import Callable, Optional

from qtpy.QtCore import QObject
from qtpy.QtGui import QDoubleValidator, QValidator
from qtpy.QtWidgets import QLayout, QLayoutItem, QLineEdit, QWidget


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


class PositiveDoubleLineEdit(QLineEdit):
    def __init__(self, parent: Optional[QWidget]) -> None:
        super().__init__(parent)
        self.setValidator(PositiveDoubleValidator())

    def setValue(self, value: float) -> None:
        text = str(value)
        state, text, _ = self.validator().validate(text, 0)
        if state != QValidator.State.Acceptable:
            raise ValueError("Value must be a positive real number.")
        if text != self.text():
            self.setText(str(value))
            self.editingFinished.emit()

    def value(self) -> float:
        return float(self.text())


def readonly_lineedit() -> QLineEdit:
    widget = QLineEdit()
    widget.setReadOnly(True)
    widget.setStyleSheet("QLineEdit{" "background: transparent;" "}")
    return widget


def update_num_widgets(
    *, layout: QLayout, desired_num: int, widget_factory: Callable[[], QWidget]
) -> None:
    current_num: int = layout.count()
    # Add any missing widgets.
    for _ in range(desired_num - current_num):
        widget = widget_factory()
        layout.addWidget(widget)
    # Remove any unneeded widgets.
    for i in range(current_num - desired_num):
        item: QLayoutItem = layout.takeAt(current_num - (i + 1))
        item.widget().deleteLater()
