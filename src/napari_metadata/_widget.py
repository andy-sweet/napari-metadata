from copy import deepcopy
from typing import TYPE_CHECKING, Optional, Tuple

from qtpy.QtWidgets import (
    QComboBox,
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
from napari_metadata._model import (
    EXTRA_METADATA_KEY,
    ExtraMetadata,
    coerce_layer_extra_metadata,
    get_layer_time_unit,
    set_layer_space_unit,
    set_layer_time_unit,
)
from napari_metadata._space_units import SpaceUnits
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

        self._attribute_widget = QWidget()
        layout.addWidget(self._attribute_widget)

        self._attribute_layout = QGridLayout()
        self._attribute_layout.setContentsMargins(0, 0, 0, 0)
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
        self._spatial_units.currentTextChanged.connect(
            self._on_spatial_units_changed
        )

        self._temporal_units = QComboBox()
        self._temporal_units.addItems(TimeUnits.names())
        self._add_attribute_row("Temporal units", self._temporal_units)
        self._temporal_units.currentTextChanged.connect(
            self._on_temporal_units_changed
        )

        restore_layout = QHBoxLayout()
        restore_layout.addStretch(1)
        self._restore_defaults = QPushButton("Restore defaults")
        self._restore_defaults.clicked.connect(self._on_restore_clicked)
        restore_layout.addWidget(self._restore_defaults)
        layout.addLayout(restore_layout)

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

    def _on_restore_clicked(self) -> None:
        if layer := self._get_selected_layer():
            metadata: ExtraMetadata = layer.metadata[EXTRA_METADATA_KEY]
            if original := metadata.original:
                metadata.axes = list(deepcopy(original.axes))
                if name := original.name:
                    layer.name = name
                if scale := original.scale:
                    layer.scale = scale
                # TODO: refactor with _on_selected_layers_changed
                self._spatial_units.set_selected_layer(layer)
                self._axes_widget.set_selected_layer(layer)
                time_unit = str(get_layer_time_unit(layer))
                self._temporal_units.setCurrentText(time_unit)

    def _on_spatial_units_changed(self):
        space_unit = SpaceUnits.from_name(self._spatial_units.currentText())
        if space_unit is None:
            space_unit = SpaceUnits.NONE
        for layer in self.viewer.layers:
            set_layer_space_unit(layer, space_unit)

    def _on_temporal_units_changed(self):
        time_unit = TimeUnits.from_name(self._temporal_units.currentText())
        if time_unit is None:
            time_unit = TimeUnits.NONE
        for layer in self.viewer.layers:
            set_layer_time_unit(layer, time_unit)

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

    def _on_name_changed(self) -> None:
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

        layer = coerce_layer_extra_metadata(self.viewer, layer)

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

        self._spatial_units.set_selected_layer(layer)
        self._axes_widget.set_selected_layer(layer)
        self._spacing_widget.set_selected_layer(layer)
        if layer is not None:
            time_unit = str(get_layer_time_unit(layer))
            self._temporal_units.setCurrentText(time_unit)

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
