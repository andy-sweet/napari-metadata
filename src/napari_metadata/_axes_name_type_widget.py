from typing import TYPE_CHECKING, Optional, Tuple, cast

from qtpy.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLayoutItem,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from napari_metadata._axis_type import AxisType

if TYPE_CHECKING:
    from napari.components import ViewerModel
    from napari.layers import Layer


class AxisNameTypeWidget(QWidget):
    def __init__(self, parent: Optional["QWidget"]) -> None:
        super().__init__(parent)
        self.name = QLineEdit()
        self.type = QComboBox()
        self.type.addItems(AxisType.names())

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.name)
        layout.addWidget(self.type)
        self.setLayout(layout)


class AxesNameTypeWidget(QWidget):
    def __init__(self, viewer: "ViewerModel") -> None:
        super().__init__()
        self._viewer: "ViewerModel" = viewer

        layout = QVBoxLayout()
        self.setLayout(layout)

        self._viewer.dims.events.axis_labels.connect(
            self._on_viewer_dims_axis_labels_changed
        )

        self.set_selected_layer(None)

    def set_selected_layer(self, layer: Optional["Layer"]) -> None:
        dims = self._viewer.dims
        self._update_num_axes(dims.ndim)
        self._set_axis_names(dims.axis_labels)
        if layer is not None:
            ndim_diff = dims.ndim - layer.ndim
            for i, widget in enumerate(self.axis_widgets()):
                widget.setEnabled(i >= ndim_diff)

    def _update_num_axes(self, num_axes: int) -> None:
        num_widgets: int = self.layout().count()
        # Add any missing widgets.
        for _ in range(num_axes - num_widgets):
            widget = self._make_axis_widget()
            self.layout().addWidget(widget)
        # Remove any unneeded widgets.
        for i in range(num_widgets - num_axes):
            item: QLayoutItem = self.layout().takeAt(num_widgets - (i + 1))
            item.widget().deleteLater()

    def _make_axis_widget(self) -> None:
        widget = AxisNameTypeWidget(self)
        widget.name.textChanged.connect(self._on_axis_name_changed)
        return widget

    def _on_viewer_dims_axis_labels_changed(self, event) -> None:
        self._set_axis_names(event.value)

    def _set_axis_names(self, names: Tuple[str, ...]) -> None:
        widgets = self.axis_widgets()
        assert len(names) == len(widgets)
        for name, widget in zip(names, widgets):
            widget.name.setText(name)

    def axis_widgets(self) -> Tuple[AxisNameTypeWidget, ...]:
        layout = self.layout()
        return [
            cast(AxisNameTypeWidget, layout.itemAt(i).widget())
            for i in range(0, layout.count())
        ]

    def axis_names(self) -> Tuple[str, ...]:
        return tuple(widget.name.text() for widget in self.axis_widgets())

    def _on_axis_name_changed(self) -> None:
        self._viewer.dims.axis_labels = self.axis_names()
