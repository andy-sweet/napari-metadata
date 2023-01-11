from functools import partial
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, Sequence

from qtpy.QtWidgets import QGridLayout, QLabel, QLineEdit, QVBoxLayout, QWidget

if TYPE_CHECKING:
    import napari
    from napari.components import Dims
    from napari.layers import Layer

# Each layer metadata attribute must define a getter and setter.
# The getter takes inputs from napari's model (e.g. the selected layer)
# and returns a string for the corresponding attribute's edit widget.
# The setter takes the string from the line edit, converts it into the
# type expected by napari's model, then updates that model with the new
# value.
# This approach encapsulates the mapping from the state of the edit
# widgets to the state of napari's model. It also allows us to provide
# custom layer metadata attribute names that can differ from napari model
# attribute names (e.g. pixel-size instead of scale).
# This design pattern should also be generalizable to more complex edit
# widgets (i.e. not just line edit widgets), but the input/output value
# will then be generic instead of all being strings.


def _get_name(layer: "Layer", dims: "Dims") -> str:
    return layer.name


def _get_dimensions(layer: "Layer", dims: "Dims") -> str:
    ndim = layer.ndim
    all_dimensions = dims.axis_labels
    return str(tuple(all_dimensions[i] for i in dims.order[-ndim:]))


def _get_pixel_size(layer: "Layer", dims: "Dims") -> str:
    return str(tuple(layer.scale))


_ATTRIBUTE_GETTERS: Dict[str, Callable[["Layer", "Dims"], Any]] = {
    "name": _get_name,
    "dimensions": _get_dimensions,
    "pixel-size": _get_pixel_size,
}


def _set_name(layer: "Layer", dims: "Dims", value: str) -> None:
    layer.name = value


def _set_dimensions(layer: "Layer", dims: "Dims", value: str) -> None:
    labels = tuple(map(_strip_dimension_label, value.strip("()").split(",")))
    _check_dimensionality(layer, labels)
    all_labels = list(dims.axis_labels)
    # Need noqa because pre-commit wants and doesn't want a space before
    # the colon.
    all_labels[-layer.ndim :] = labels  # noqa
    dims.axis_labels = all_labels


def _strip_dimension_label(label: str) -> str:
    # TODO: strip whitespace and string quotes with one call.
    return label.strip().strip("'\"")


def _set_pixel_size(layer: "Layer", dims: "Dims", value: str) -> None:
    scale = tuple(map(float, value.strip("()").split(",")))
    _check_dimensionality(layer, scale)
    layer.scale = scale


def _check_dimensionality(layer: "Layer", values: Sequence) -> None:
    if len(values) != layer.ndim:
        raise RuntimeError(
            f"Number of values ({len(values)}) does "
            f"not match layer dimensionality ({layer.ndim})."
        )


_ATTRIBUTE_SETTERS: Dict[str, Callable[["Layer", "Dims", str], None]] = {
    "name": _set_name,
    "dimensions": _set_dimensions,
    "pixel-size": _set_pixel_size,
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

        # TODO: need to respond to changes to the relevant model state of the
        # currently selected layer. We could do this by connecting to those
        # events in _on_selected_layers_changed (and disconnecting old ones).

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
        self._add_attribute_widgets("pixel-size", editable=True)

        self._on_selected_layers_changed()

    def _add_attribute_widgets(
        self, name: str, *, editable: bool = False
    ) -> None:
        value_edit = QLineEdit("")
        value_edit.setEnabled(editable)
        value_edit.editingFinished.connect(
            partial(self._on_attribute_text_changed, name)
        )
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

    def _get_selected_layer(self) -> Optional["Layer"]:
        selection = self.viewer.layers.selection
        return next(iter(selection)) if len(selection) > 0 else None

    def _update_attribute(self, layer: "Layer", name: str) -> None:
        text = _ATTRIBUTE_GETTERS[name](layer, self.viewer.dims)
        self._value_edits[name].setText(text)

    def _on_attribute_text_changed(self, name: str) -> None:
        if layer := self._get_selected_layer():
            text = self._value_edits[name].text()
            _ATTRIBUTE_SETTERS[name](layer, self.viewer.dims, text)

    def _on_dims_axis_labels_changed(self) -> None:
        if layer := self._get_selected_layer():
            self._update_attribute(layer, "dimensions")
