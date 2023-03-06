from qtpy.QtWidgets import QLineEdit


def readonly_lineedit() -> QLineEdit:
    widget = QLineEdit()
    widget.setReadOnly(True)
    widget.setStyleSheet("QLineEdit{" "background: transparent;" "}")
    return widget
