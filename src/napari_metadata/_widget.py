import os
from functools import partial
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, Sequence

import napari_ome_zarr
import zarr
from ome_zarr.io import parse_url
from ome_zarr.writer import write_image
from qtpy.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    import napari
    from napari.components import ViewerModel
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


def _get_name(layer: "Layer", viewer: "ViewerModel") -> str:
    return layer.name


def _get_file_path(layer: "Layer", viewer: "ViewerModel") -> str:
    return str(layer.source.path)


def _get_plugin(layer: "Layer", viewer: "ViewerModel") -> str:
    source = layer.source
    return (
        str(source.reader_plugin)
        if source.sample is None
        else str(source.sample)
    )


def _get_data_size(layer: "Layer", viewer: "ViewerModel") -> str:
    return str(layer.data.shape)


def _get_dimensions(layer: "Layer", viewer: "ViewerModel") -> str:
    ndim = layer.ndim
    dims = viewer.dims
    all_dimensions = dims.axis_labels
    return str(tuple(all_dimensions[i] for i in dims.order[-ndim:]))


def _get_pixel_size(layer: "Layer", viewer: "ViewerModel") -> str:
    return str(tuple(layer.scale))


def _get_pixel_size_unit(layer: "Layer", viewer: "ViewerModel") -> str:
    return str(viewer.scale_bar.unit)


def _get_pixel_type(layer: "Layer", viewer: "ViewerModel") -> str:
    return str(layer.data.dtype)


_ATTRIBUTE_GETTERS: Dict[str, Callable[["Layer", "ViewerModel"], Any]] = {
    "name": _get_name,
    "file-path": _get_file_path,
    "plugin": _get_plugin,
    "data-size": _get_data_size,
    "dimensions": _get_dimensions,
    "pixel-size": _get_pixel_size,
    "pixel-size-unit": _get_pixel_size_unit,
    "pixel-type": _get_pixel_type,
}


def _set_name(layer: "Layer", viewer: "ViewerModel", value: str) -> None:
    layer.name = value


def _set_file_path(layer: "Layer", viewer: "ViewerModel", value: str) -> None:
    raise NotImplementedError("File path cannot be changed.")


def _set_plugin(layer: "Layer", viewer: "ViewerModel", value: str) -> None:
    raise NotImplementedError("Plugin cannot be changed.")


def _set_data_size(layer: "Layer", viewer: "ViewerModel", value: str) -> None:
    raise NotImplementedError("Data size cannot be changed.")


def _set_dimensions(layer: "Layer", viewer: "ViewerModel", value: str) -> None:
    labels = tuple(map(_strip_dimension_label, value.strip("()").split(",")))
    _check_dimensionality(layer, labels)
    dims = viewer.dims
    all_labels = list(dims.axis_labels)
    # Need noqa because pre-commit wants and doesn't want a space before
    # the colon.
    all_labels[-layer.ndim :] = labels  # noqa
    dims.axis_labels = all_labels


def _strip_dimension_label(label: str) -> str:
    # TODO: strip whitespace and string quotes with one call.
    return label.strip().strip("'\"")


def _set_pixel_size(layer: "Layer", viewer: "ViewerModel", value: str) -> None:
    scale = tuple(map(float, value.strip("()").split(",")))
    _check_dimensionality(layer, scale)
    layer.scale = scale


def _set_pixel_size_unit(
    layer: "Layer", viewer: "ViewerModel", value: str
) -> None:
    # TODO: coercion from None should be really handled gracefully by napari
    # because the declared type of the field is Optional[str].
    if value.lower() in {"", "none", "pixel", "pixels"}:
        value = None
    viewer.scale_bar.unit = value


def _set_pixel_type(layer: "Layer", viewer: "ViewerModel", value: str) -> None:
    raise NotImplementedError("Pixel type cannot be changed.")


def _check_dimensionality(layer: "Layer", values: Sequence) -> None:
    if len(values) != layer.ndim:
        raise RuntimeError(
            f"Number of values ({len(values)}) does "
            f"not match layer dimensionality ({layer.ndim})."
        )


_ATTRIBUTE_SETTERS: Dict[
    str, Callable[["Layer", "ViewerModel", str], None]
] = {
    "name": _set_name,
    "file-path": _set_file_path,
    "plugin": _set_plugin,
    "data-size": _set_data_size,
    "dimensions": _set_dimensions,
    "pixel-size": _set_pixel_size,
    "pixel-size-unit": _set_pixel_size_unit,
    "pixel-type": _set_pixel_type,
}


class QMetadataWidget(QWidget):
    def __init__(self, viewer: "napari.viewer.Viewer"):
        super().__init__()
        self._value_edits = {}
        self.viewer = viewer
        self._selected_layer = None

        self.viewer.layers.selection.events.changed.connect(
            self._on_selected_layers_changed
        )

        self.viewer.dims.events.axis_labels.connect(
            self._on_dims_axis_labels_changed
        )

        self.viewer.scale_bar.events.unit.connect(
            self._on_scale_bar_units_changed
        )

        layout = QVBoxLayout()
        self.setLayout(layout)

        description = QLabel("Open and save a layer with metadata")
        layout.addWidget(description)

        self._io_widget = QWidget()
        io_layout = QHBoxLayout()
        self._io_widget.setLayout(io_layout)

        self._open_button = QPushButton("Open layer")
        self._open_button.clicked.connect(self._on_open_clicked)
        io_layout.addWidget(self._open_button)

        self._save_button = QPushButton("Save layer")
        self._save_button.clicked.connect(self._on_save_clicked)
        io_layout.addWidget(self._save_button)

        layout.addWidget(self._io_widget)

        description = QLabel("View and edit layer metadata values")
        layout.addWidget(description)

        self._attribute_widget = QWidget()
        layout.addWidget(self._attribute_widget)

        self._attribute_layout = QGridLayout()
        self._attribute_widget.setLayout(self._attribute_layout)
        self._add_attribute_widgets("name", editable=True)
        self._add_attribute_widgets("file-path", editable=False)
        self._add_attribute_widgets("plugin", editable=False)
        self._add_attribute_widgets("data-size", editable=False)
        self._add_attribute_widgets("dimensions", editable=True)
        self._add_attribute_widgets("pixel-size", editable=True)
        self._add_attribute_widgets("pixel-size-unit", editable=True)
        self._add_attribute_widgets("pixel-type", editable=False)

        self._on_selected_layers_changed()

    def _add_attribute_widgets(self, name: str, *, editable: bool) -> None:
        value_edit = QLineEdit("")
        # TODO: consider changing this to setReadOnly, though that triggers
        # editingFinished, which may raise an error.
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
        layer = self._get_selected_layer()

        if layer == self._selected_layer:
            # TODO: check if this can actually occur.
            return

        # TODO: declare dependency between metadata attribute and layer state
        # to make connections more automatic.
        if self._selected_layer is not None:
            self._selected_layer.events.name.disconnect(
                self._on_selected_layer_name_changed
            )
            self._selected_layer.events.data.disconnect(
                self._on_selected_layer_data_changed
            )
            self._selected_layer.events.scale.disconnect(
                self._on_selected_layer_scale_changed
            )

        if layer is not None:
            layer.events.name.connect(self._on_selected_layer_name_changed)
            layer.events.data.connect(self._on_selected_layer_data_changed)
            layer.events.scale.connect(self._on_selected_layer_scale_changed)
            for name in self._value_edits:
                self._update_attribute(layer, name)
            self._attribute_widget.show()
        else:
            self._attribute_widget.hide()

        self._selected_layer = layer

    def _get_selected_layer(self) -> Optional["Layer"]:
        selection = self.viewer.layers.selection
        return next(iter(selection)) if len(selection) > 0 else None

    def _update_attribute(self, layer: "Layer", name: str) -> None:
        text = _ATTRIBUTE_GETTERS[name](layer, self.viewer)
        self._value_edits[name].setText(text)

    def _on_attribute_text_changed(self, name: str) -> None:
        if layer := self._get_selected_layer():
            text = self._value_edits[name].text()
            _ATTRIBUTE_SETTERS[name](layer, self.viewer, text)

    def _on_dims_axis_labels_changed(self) -> None:
        if layer := self._get_selected_layer():
            self._update_attribute(layer, "dimensions")

    def _on_scale_bar_units_changed(self) -> None:
        if layer := self._get_selected_layer():
            self._update_attribute(layer, "pixel-size-unit")

    def _on_selected_layer_name_changed(self) -> None:
        if layer := self._get_selected_layer():
            self._update_attribute(layer, "name")

    def _on_selected_layer_data_changed(self) -> None:
        if layer := self._get_selected_layer():
            self._update_attribute(layer, "data-size")
            self._update_attribute(layer, "pixel-type")

    def _on_selected_layer_scale_changed(self) -> None:
        if layer := self._get_selected_layer():
            self._update_attribute(layer, "pixel-size")

    def _on_open_clicked(self) -> None:
        path = QFileDialog.getExistingDirectory(
            parent=self,
            caption="Open napari layer with metadata",
        )

        # TODO: understand if path is Optional[str] or str.
        if path is None or len(path) == 0:
            return

        # TODO: consider using ome_zarr Reader directly to have more control
        # here for reading multiple layers.
        if reader := napari_ome_zarr.napari_get_reader(path):
            for layer_tuple in reader(path):
                # TODO: any public version of this?
                self.viewer._add_layer_from_data(*layer_tuple)

        # Read viewer wide metadata after adding layers so that axis labels
        # are not trimmed.
        with zarr.open(path, mode="r") as root:
            viewer_meta = root["napari"]
            self.viewer.scale_bar.unit = viewer_meta.attrs["unit"]
            self.viewer.dims.axis_labels = viewer_meta.attrs["axis_labels"]

    def _on_save_clicked(self) -> None:
        path, format = QFileDialog.getSaveFileName(
            parent=self,
            caption="Save napari layer with metadata",
            filter="napari layer (*.zapari)",
        )
        if path is None:
            return

        layer = self._get_selected_layer()
        if layer is None:
            return

        # From https://ome-zarr.readthedocs.io/en/stable/python.html#writing-ome-ngff-images # noqa

        os.mkdir(path)

        store = parse_url(path, mode="w").store
        root = zarr.group(store=store)

        viewer_meta = root.create_group("napari")
        viewer_meta.attrs["unit"] = self.viewer.scale_bar.unit
        viewer_meta.attrs["axis_labels"] = self.viewer.dims.axis_labels

        # Need noqa because pre-commit wants and doesn't want a space before
        # the colon.
        layer_axes = self.viewer.dims.axis_labels[-layer.ndim :]  # noqa
        write_image(
            image=layer.data,
            group=root,
            axes=layer_axes,
        )
