from typing import Callable, List, Optional, Protocol, Tuple

from qtpy.QtWidgets import QGridLayout, QLineEdit, QWidget


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
