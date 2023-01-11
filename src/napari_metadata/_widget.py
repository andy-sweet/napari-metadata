from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, Tuple

import numpy as np
from qtpy.QtWidgets import QGridLayout, QLabel, QLineEdit, QVBoxLayout, QWidget

if TYPE_CHECKING:
    import napari
    from napari.components import Dims
    from napari.layers import Layer


def _get_name(layer: "Layer", dims: "Dims") -> str:
    return layer.name


def _get_dimensions(layer: "Layer", dims: "Dims") -> Tuple[str]:
    ndim = layer.ndim
    all_dimensions = dims.axis_labels
    return tuple(all_dimensions[i] for i in dims.order[-ndim:])


def _get_scale(layer: "Layer", dims: "Dims") -> Tuple[float]:
    return tuple(layer.scale)


_ATTRIBUTE_GETTERS: Dict[str, Callable[["Layer", "Dims"], Any]] = {
    "name": _get_name,
    "dimensions": _get_dimensions,
    "scale": _get_scale,
}


class QMetadataWidget(QWidget):
    def __init__(self, viewer: "napari.viewer.Viewer"):
        super().__init__()
        self._value_edits = {}
        self.viewer = viewer

        self.viewer.layers.selection.events.changed.connect(
            self._on_selected_layers_changed
        )

        self.viewer.dims.events.axis_labels.connect(
            self._on_dims_axis_labels_changed
        )

        layout = QVBoxLayout()
        self.setLayout(layout)

        description = QLabel("View and edit layer metadata values")
        layout.addWidget(description)

        self._attribute_widget = QWidget()
        layout.addWidget(self._attribute_widget)

        self._attribute_layout = QGridLayout()
        self._attribute_widget.setLayout(self._attribute_layout)
        self._add_attribute_widgets("name")
        self._add_attribute_widgets("dimensions", editable=True)
        self._add_attribute_widgets("scale", editable=True)
        self._value_edits["scale"].editingFinished.connect(
            self._on_scale_changed
        )

        self._on_selected_layers_changed()

    def _add_attribute_widgets(
        self, name: str, *, editable: bool = False
    ) -> None:
        value_edit = QLineEdit("")
        value_edit.setEnabled(editable)
        layout = self._attribute_widget.layout()
        row = layout.rowCount()
        layout.addWidget(QLabel(name), row, 0)
        layout.addWidget(value_edit, row, 1)
        self._value_edits[name] = value_edit

    def _on_selected_layers_changed(self) -> None:
        if layer := self._get_selected_layer():
            for name in self._value_edits:
                self._update_attribute(layer, name)
            self._attribute_widget.show()
        else:
            self._attribute_widget.hide()

    def _update_attribute(self, layer: "Layer", name: str) -> None:
        value = _ATTRIBUTE_GETTERS[name](layer, self.viewer.dims)
        self._value_edits[name].setText(str(value))

    def _on_dims_axis_labels_changed(self) -> None:
        if layer := self._get_selected_layer():
            self._update_attribute(layer, "dimensions")

    def _get_selected_layer(self) -> Optional["Layer"]:
        selection = self.viewer.layers.selection
        return next(iter(selection)) if len(selection) > 0 else None

    def _on_scale_changed(self) -> None:
        if layer := self._get_selected_layer():
            text = self._value_edits["scale"].text()
            value = np.fromstring(text.strip("()"), sep=",")
            layer.scale = value
