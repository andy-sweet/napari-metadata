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
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from napari_metadata._axes_name_type_widget import AxesNameTypeWidget
from napari_metadata._axes_spacing_widget import AxesSpacingWidget
from napari_metadata._model import coerce_layer_extra_metadata
from napari_metadata._spatial_units_combo_box import SpatialUnitsComboBox
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

        layout.addWidget(QLabel("Open and save a layer with metadata"))

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

        layout.addWidget(QLabel("View and edit selected layer metadata"))

        self._attribute_widget = QWidget()
        layout.addWidget(self._attribute_widget)

        self._attribute_layout = QGridLayout()
        self._attribute_widget.setLayout(self._attribute_layout)

        self._name = QLineEdit()
        self._add_attribute_row("Channel name", self._name)
        self._name.textChanged.connect(self._on_name_changed)

        self._file_path = self._add_readonly_attribute_row("File name")
        self._plugin = self._add_readonly_attribute_row("Plugin")
        self._data_shape = self._add_readonly_attribute_row("Array shape")
        self._data_type = self._add_readonly_attribute_row("Data type")

        self._axes_widget = AxesNameTypeWidget(napari_viewer)
        self._add_attribute_row("Dimensions", self._axes_widget)

        self._spacing_widget = AxesSpacingWidget(napari_viewer)
        self._add_attribute_row("Spacing", self._spacing_widget)

        self._spatial_units = SpatialUnitsComboBox(napari_viewer)
        self._add_attribute_row("Spatial units", self._spatial_units)
        # self._spatial_units.currentTextChanged.connect(self._on_spatial_units_changed)

        self._temporal_units = QComboBox()
        self._temporal_units.addItems(TimeUnits.names())
        self._add_attribute_row("Temporal units", self._temporal_units)
        # self._temporal_units.currentTextChanged.connect(self._on_temporal_units_changed)

        layout.addStretch(1)

        view_controls = QHBoxLayout()
        self._show_full = QPushButton()
        self._show_full.setChecked(False)
        self._show_full.setCheckable(True)
        self._show_full.toggled.connect(self._on_show_full_toggled)

        view_controls.addWidget(self._show_full)
        view_controls.addStretch(1)
        self._close_button = QPushButton()
        # TODO: dock widget should be closed when clicked.
        view_controls.addWidget(self._close_button)

        self._on_show_full_toggled()

        layout.addLayout(view_controls)

        self._on_selected_layers_changed()

    def _on_show_full_toggled(self) -> None:
        show_full = self._show_full.isChecked()
        if show_full:
            self._show_full.setText("View editable metadata")
            self._close_button.setText("Close")
        else:
            self._show_full.setText("View full metadata")
            self._close_button.setText("Cancel")

        for row in range(self._attribute_layout.rowCount()):
            item = self._attribute_layout.itemAtPosition(row, 1)
            if item is not None:
                widget = item.widget()
                if isinstance(widget, QLineEdit) and widget.isReadOnly():
                    self._set_attribute_row_visible(row, show_full)

    def _on_name_changed(self):
        if layer := self._get_selected_layer():
            layer.name = self._name.text()

    def _set_attribute_row_visible(self, row: int, visible: bool) -> None:
        for column in range(self._attribute_layout.columnCount()):
            item = self._attribute_layout.itemAtPosition(row, column)
            item.widget().setVisible(visible)

    def _add_attribute_row(self, name: str, widget: QWidget) -> None:
        layout = self._attribute_widget.layout()
        row = layout.rowCount()
        layout.addWidget(QLabel(name), row, 0)
        layout.addWidget(widget, row, 1)

    def _add_readonly_attribute_row(self, name: str) -> None:
        widget = QLineEdit()
        widget.setReadOnly(True)
        self._add_attribute_row(name, widget)
        return widget

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

        layer = coerce_layer_extra_metadata(layer)

        if layer is not None:
            self._name.setText(layer.name)
            self._file_path.setText(str(layer.source.path))
            self._plugin.setText(self._get_plugin_info(layer))
            self._data_shape.setText(str(layer.data.shape))
            self._data_type.setText(str(layer.data.dtype))

            layer.events.name.connect(self._on_selected_layer_name_changed)
            layer.events.data.connect(self._on_selected_layer_data_changed)

            self._attribute_widget.show()
        else:
            self._attribute_widget.hide()

        self._axes_widget.set_selected_layer(layer)
        self._spacing_widget.set_selected_layer(layer)

        self._selected_layer = layer

    def _get_axis_names(self, layer: "Layer") -> Tuple[str, ...]:
        return self._axes_widget._layer_axis_names(layer)

    def _get_plugin_info(self, layer: "Layer") -> str:
        source = layer.source
        return (
            str(source.reader_plugin)
            if source.sample is None
            else str(source.sample)
        )

    def _get_selected_layer(self) -> Optional["Layer"]:
        selection = self.viewer.layers.selection
        return next(iter(selection)) if len(selection) > 0 else None

    def _on_selected_layer_name_changed(self) -> None:
        if layer := self._get_selected_layer():
            self._name.setText(layer.name)

    def _on_selected_layer_data_changed(self) -> None:
        if layer := self._get_selected_layer():
            self._data_shape.setText(str(layer.data.shape))
            self._data_type.setText(str(layer.data.dtype))

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
