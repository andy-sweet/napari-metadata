import os
from typing import TYPE_CHECKING, Optional, Tuple

import napari_ome_zarr
import zarr
from ome_zarr.io import parse_url
from ome_zarr.writer import write_image
from qtpy.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGridLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from napari_metadata._axes_name_type_widget import AxesNameTypeWidget
from napari_metadata._axes_spacing_widget import AxesSpacingWidget
from napari_metadata._axes_type_units_widget import SpatialUnitsComboBox
from napari_metadata._time_units import TimeUnits

if TYPE_CHECKING:
    from napari.components import ViewerModel
    from napari.layers import Layer


class QMetadataWidget(QWidget):
    def __init__(self, napari_viewer: "ViewerModel"):
        super().__init__()
        self.viewer = napari_viewer
        self._selected_layer = None

        self.viewer.layers.selection.events.changed.connect(
            self._on_selected_layers_changed
        )

        layout = QVBoxLayout()
        self.setLayout(layout)

        # TODO: add these back later when supporting open/save.
        # description = QLabel("Open and save a layer with metadata")
        # layout.addWidget(description)

        # self._io_widget = QWidget()
        # io_layout = QHBoxLayout()
        # self._io_widget.setLayout(io_layout)

        # self._open_button = QPushButton("Open layer")
        # self._open_button.clicked.connect(self._on_open_clicked)
        # io_layout.addWidget(self._open_button)

        # self._save_button = QPushButton("Save layer")
        # self._save_button.clicked.connect(self._on_save_clicked)
        # io_layout.addWidget(self._save_button)

        # layout.addWidget(self._io_widget)

        self._attribute_widget = QWidget()
        layout.addWidget(self._attribute_widget)

        self._attribute_layout = QGridLayout()
        self._attribute_widget.setLayout(self._attribute_layout)

        self._name = QLineEdit()
        self._add_attribute_row("Channel name", self._name)
        self._name.textChanged.connect(self._on_name_changed)

        self._axes_widget = AxesNameTypeWidget(napari_viewer)
        self._add_attribute_row("Dimensions", self._axes_widget)

        self._spacing_widget = AxesSpacingWidget()
        self._add_attribute_row("Spacing", self._spacing_widget)

        self._spatial_units = SpatialUnitsComboBox(napari_viewer)
        self._spatial_units.currentTextChanged.connect(
            self._on_space_unit_changed
        )
        self._add_attribute_row("Spatial units", self._spatial_units)

        self._temporal_units = QComboBox()
        self._temporal_units.addItems(TimeUnits.names())
        self._add_attribute_row("Temporal units", self._temporal_units)

        self._on_selected_layers_changed()

    def _on_name_changed(self):
        if layer := self._get_selected_layer():
            layer.name = self._name.text()

    def _on_space_unit_changed(self):
        if layer := self._get_selected_layer():
            layer_axis_units = self._get_layer_axis_units(layer)
            self._spacing_widget.set_axis_units(layer_axis_units)

    def _add_attribute_row(self, name: str, widget: QWidget) -> None:
        layout = self._attribute_widget.layout()
        row = layout.rowCount()
        layout.addWidget(QLabel(name), row, 0)
        layout.addWidget(widget, row, 1)

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

        if layer is not None:
            layer.events.name.connect(self._on_selected_layer_name_changed)
            self._on_selected_layer_name_changed()
            self._attribute_widget.show()
        else:
            self._attribute_widget.hide()

        self._axes_widget.set_selected_layer(layer)

        self._spacing_widget.set_selected_layer(layer)

        layer_axis_widgets = self._axes_widget._layer_axis_widgets(layer)
        layer_axis_names = tuple(w.name.text() for w in layer_axis_widgets)
        self._spacing_widget.set_axis_names(layer_axis_names)

        layer_axis_units = self._get_layer_axis_units(layer)
        self._spacing_widget.set_axis_units(layer_axis_units)

        self._selected_layer = layer

    def _get_layer_axis_units(self, layer: "Layer") -> Tuple[str, ...]:
        layer_axis_widgets = self._axes_widget._layer_axis_widgets(layer)
        layer_axis_units = []
        space_unit = self._spatial_units.currentText()
        time_unit = self._temporal_units.currentText()
        for widget in layer_axis_widgets:
            unit = ""
            axis_type = widget.type.currentText()
            if axis_type == "space":
                unit = space_unit
            elif axis_type == "time":
                unit = time_unit
            layer_axis_units.append(unit)
        return layer_axis_units

    def _get_axis_names(self, layer) -> Tuple[str, ...]:
        return self._axes_widget._layer_axis_names(layer)

    def _get_selected_layer(self) -> Optional["Layer"]:
        selection = self.viewer.layers.selection
        return next(iter(selection)) if len(selection) > 0 else None

    def _on_selected_layer_name_changed(self) -> None:
        if layer := self._get_selected_layer():
            self._name.setText(layer.name)

    def _on_open_clicked(self) -> None:
        path = QFileDialog.getExistingDirectory(
            parent=self,
            caption="Open napari layer with metadata",
            options=QFileDialog.DontUseNativeDialog,
        )

        # TODO: understand if path is Optional[str] or str.
        if path is None or len(path) == 0:
            return

        # TODO: consider using ome_zarr Reader directly to have more control
        # here for reading multiple layers.
        if reader := napari_ome_zarr.napari_get_reader(path):
            for layer_tuple in reader(path):
                # TODO: could use public Layer.create, but that requires
                # importing Layer and explicitly depending on napari.
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
            filter="napari layer (*.zarr)",
            options=QFileDialog.DontUseNativeDialog,
        )
        # TODO: understand if path is Optional[str] or str.
        if path is None or len(path) == 0:
            return

        # TODO: I thought QFileDialog did this automatically, but maybe not?
        path = path if path.endswith(".zarr") else path + ".zarr"

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
