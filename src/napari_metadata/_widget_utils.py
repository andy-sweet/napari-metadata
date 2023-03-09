from typing import Callable

from qtpy.QtWidgets import QLayout, QLayoutItem, QLineEdit, QWidget


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
