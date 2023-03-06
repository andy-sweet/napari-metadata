from copy import deepcopy
from typing import TYPE_CHECKING, Optional

from qtpy.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from napari_metadata._axes_name_type_widget import (
    AxesNameTypeWidget,
    ReadOnlyAxesNameTypeWidget,
)
from napari_metadata._axes_spacing_widget import (
    AxesSpacingWidget,
    ReadOnlyAxesSpacingWidget,
)
from napari_metadata._model import (
    EXTRA_METADATA_KEY,
    ExtraMetadata,
    coerce_layer_extra_metadata,
    get_layer_space_unit,
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


class EditableMetadataWidget(QWidget):
    def __init__(self, viewer: "ViewerModel") -> None:
        super().__init__()
        self._viewer = viewer
        self._selected_layer = None
        layout = QVBoxLayout()
        self.setLayout(layout)

        self._attribute_widget = QWidget()
        layout.addWidget(self._attribute_widget)

        self._attribute_layout = QGridLayout()
        self._attribute_layout.setContentsMargins(0, 0, 0, 0)
        self._attribute_widget.setLayout(self._attribute_layout)

        self.name = QLineEdit()
        self._add_attribute_row("Layer name", self.name)
        self.name.textChanged.connect(self._on_name_changed)

        self._axes_widget = AxesNameTypeWidget(viewer)
        self._add_attribute_row("Dimensions", self._axes_widget)

        self._spacing_widget = AxesSpacingWidget(viewer)
        self._add_attribute_row("Spacing", self._spacing_widget)

        self._spatial_units = SpatialUnitsComboBox(viewer)
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
        self._restore_defaults.setStyleSheet(
            "QPushButton {" "color: #898D93;" "background: transparent;" "}"
        )
        self._restore_defaults.clicked.connect(self._on_restore_clicked)
        restore_layout.addWidget(self._restore_defaults)
        layout.addLayout(restore_layout)

        # Push control widget to bottom.
        layout.addStretch(1)

        self._control_widget = QWidget()
        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(0, 0, 0, 0)
        self._control_widget.setLayout(control_layout)

        self.show_readonly = QPushButton("View full metadata")
        self.show_readonly.setStyleSheet(
            "QPushButton {" "color: #66C1FF;" "background: transparent;" "}"
        )

        control_layout.addWidget(self.show_readonly)
        control_layout.addStretch(1)
        self.cancel_button = QPushButton("Cancel")
        control_layout.addWidget(self.cancel_button)
        # TODO: save is in designs, but unclear if we should really
        # allow in-place saving given napari reader/writer model.
        self._save_button = QPushButton("Save")
        self._save_button.setEnabled(False)
        control_layout.addWidget(self._save_button)

        layout.addWidget(self._control_widget)

    def set_selected_layer(self, layer: Optional["Layer"]) -> None:
        if layer == self._selected_layer:
            return

        if self._selected_layer is not None:
            self._selected_layer.events.name.disconnect(
                self._on_selected_layer_name_changed
            )

        if layer is not None:
            layer.events.name.connect(self._on_selected_layer_name_changed)

        self._spatial_units.set_selected_layer(layer)
        self._axes_widget.set_selected_layer(layer)
        self._spacing_widget.set_selected_layer(layer)
        if layer is not None:
            self.name.setText(layer.name)
            time_unit = str(get_layer_time_unit(layer))
            self._temporal_units.setCurrentText(time_unit)

        self._selected_layer = layer

    def _add_attribute_row(self, name: str, widget: QWidget) -> None:
        layout = self._attribute_widget.layout()
        row = layout.rowCount()
        layout.addWidget(QLabel(name), row, 0)
        layout.addWidget(widget, row, 1)

    def _on_selected_layer_name_changed(self, event) -> None:
        # TODO: find a more reliable way to do this.
        self.name.setText(event.source.name)

    def _on_name_changed(self) -> None:
        if layer := _get_selected_layer(self._viewer):
            layer.name = self.name.text()

    def _on_spatial_units_changed(self):
        space_unit = SpaceUnits.from_name(self._spatial_units.currentText())
        if space_unit is None:
            space_unit = SpaceUnits.NONE
        for layer in self._viewer.layers:
            set_layer_space_unit(layer, space_unit)

    def _on_temporal_units_changed(self):
        time_unit = TimeUnits.from_name(self._temporal_units.currentText())
        if time_unit is None:
            time_unit = TimeUnits.NONE
        for layer in self._viewer.layers:
            set_layer_time_unit(layer, time_unit)

    def _on_restore_clicked(self) -> None:
        if layer := _get_selected_layer(self._viewer):
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


class ReadOnlyMetadataWidget(QWidget):
    def __init__(self, viewer: "ViewerModel") -> None:
        super().__init__()
        self._viewer = viewer
        self._selected_layer = None
        layout = QVBoxLayout()
        self.setLayout(layout)

        self._attribute_widget = QWidget()
        layout.addWidget(self._attribute_widget)

        self._attribute_layout = QGridLayout()
        self._attribute_layout.setContentsMargins(0, 0, 0, 0)
        self._attribute_widget.setLayout(self._attribute_layout)

        item_label = QLabel("Item")
        item_label.setStyleSheet("font-weight: bold")
        self._attribute_layout.addWidget(item_label, 0, 0)
        value_label = QLabel("Value")
        value_label.setStyleSheet("font-weight: bold")
        self._attribute_layout.addWidget(value_label, 0, 1)

        self.name = self._add_attribute_row("Layer name")
        self.file_path = self._add_attribute_row("File name")
        self.plugin = self._add_attribute_row("Plugin")
        self.data_shape = self._add_attribute_row("Array shape")
        self.data_type = self._add_attribute_row("Data type")

        self._axes_widget = ReadOnlyAxesNameTypeWidget(viewer)
        self._add_attribute_row("Dimensions", self._axes_widget)

        self._spacing_widget = ReadOnlyAxesSpacingWidget(viewer)
        self._add_attribute_row("Spacing", self._spacing_widget)

        self.spatial_units = self._add_attribute_row("Spatial units")
        self.temporal_units = self._add_attribute_row("Temporal units")

        # Push control widget to bottom.
        layout.addStretch(1)

        self._control_widget = QWidget()
        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(0, 0, 0, 0)
        self._control_widget.setLayout(control_layout)

        self.show_editable = QPushButton("View editable metadata")
        self.show_editable.setStyleSheet(
            "QPushButton {" "color: #66C1FF;" "background: transparent;" "}"
        )

        control_layout.addWidget(self.show_editable)
        control_layout.addStretch(1)
        self.close_button = QPushButton("Close")
        control_layout.addWidget(self.close_button)

        layout.addWidget(self._control_widget)

    def set_selected_layer(self, layer: Optional["Layer"]) -> None:
        if layer == self._selected_layer:
            return

        if self._selected_layer is not None:
            self._selected_layer.events.name.disconnect(
                self._on_selected_layer_name_changed
            )
            self._selected_layer.events.data.disconnect(
                self._on_selected_layer_data_changed
            )

        if layer is not None:
            self.name.setText(layer.name)
            self.file_path.setText(str(layer.source.path))
            self.plugin.setText(self._get_plugin_info(layer))
            self.data_shape.setText(str(layer.data.shape))
            self.data_type.setText(str(layer.data.dtype))
            self.spatial_units.setText(str(get_layer_space_unit(layer)))
            self.temporal_units.setText(str(get_layer_time_unit(layer)))

            layer.events.name.connect(self._on_selected_layer_name_changed)
            layer.events.data.connect(self._on_selected_layer_data_changed)

        self._axes_widget.set_selected_layer(layer)
        self._spacing_widget.set_selected_layer(layer)

        self._selected_layer = layer

    def set_spatial_units(self, units: str) -> None:
        self.spatial_units.setText(units)

    def set_temporal_units(self, units: str) -> None:
        self.temporal_units.setText(units)

    def _add_attribute_row(
        self, name: str, widget: Optional[QWidget] = None
    ) -> QWidget:
        layout = self._attribute_widget.layout()
        row = layout.rowCount()
        layout.addWidget(QLabel(name), row, 0)
        if widget is None:
            widget = QLineEdit()
            widget.setReadOnly(True)
            widget.setStyleSheet("QLineEdit{" "background: transparent;" "}")
        layout.addWidget(widget, row, 1)
        return widget

    def _on_selected_layer_name_changed(self, event) -> None:
        # TODO: find a more reliable way to do this.
        self.name.setText(event.source.name)

    def _on_selected_layer_data_changed(self, event) -> None:
        data = event.value
        self.data_shape.setText(str(data.shape))
        self.data_type.setText(str(data.dtype))

    def _get_plugin_info(self, layer: "Layer") -> str:
        source = layer.source
        return (
            str(source.reader_plugin)
            if source.sample is None
            else str(source.sample)
        )


class ReadOnlyAxisTypeWidget(QWidget):
    def __init__(self, viewer: "ViewerModel") -> None:
        super().__init__()

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)


class InfoWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        info_label = QLabel("Select a single layer to view its metadata")
        layout.addWidget(info_label)
        layout.addStretch(1)
        self.setLayout(layout)


class QMetadataWidget(QStackedWidget):
    def __init__(self, napari_viewer: "ViewerModel"):
        super().__init__()
        self.viewer = napari_viewer
        self._selected_layer = None

        self._info_widget = InfoWidget()
        self.addWidget(self._info_widget)

        self._editable_widget = EditableMetadataWidget(napari_viewer)
        self._editable_widget.show_readonly.clicked.connect(
            self._show_readonly
        )
        self._editable_widget.cancel_button.clicked.connect(
            self._remove_dock_widget
        )
        self.addWidget(self._editable_widget)

        self._readonly_widget = ReadOnlyMetadataWidget(napari_viewer)
        self._readonly_widget.show_editable.clicked.connect(
            self._show_editable
        )
        self._readonly_widget.close_button.clicked.connect(
            self._remove_dock_widget
        )
        self.addWidget(self._readonly_widget)

        self._editable_widget._spatial_units.currentTextChanged.connect(
            self._readonly_widget.set_spatial_units
        )
        self._editable_widget._temporal_units.currentTextChanged.connect(
            self._readonly_widget.set_temporal_units
        )

        self.viewer.layers.selection.events.changed.connect(
            self._on_selected_layers_changed
        )

        self._on_selected_layers_changed()

    def _show_readonly(self) -> None:
        self.setCurrentWidget(self._readonly_widget)

    def _show_editable(self) -> None:
        self.setCurrentWidget(self._editable_widget)

    def _on_selected_layers_changed(self) -> None:
        layer = _get_selected_layer(self.viewer)

        if layer is None:
            self.setCurrentWidget(self._info_widget)
        else:
            self.setCurrentWidget(self._editable_widget)

        # This can occur when there is no selected layer at initialization,
        # so do some things must be done before this.
        if layer == self._selected_layer:
            return

        layer = coerce_layer_extra_metadata(self.viewer, layer)

        # TODO: readonly first since editable may make changes to the napari
        # data model (e.g. axis_labels).
        self._readonly_widget.set_selected_layer(layer)
        self._editable_widget.set_selected_layer(layer)

        self._selected_layer = layer

    def _remove_dock_widget(self) -> None:
        # TODO: make this less fragile, but also don't require a full
        # viewer for tests.
        if window := getattr(self.viewer, "window", None):
            window.remove_dock_widget(self)


def _get_selected_layer(viewer: "ViewerModel") -> Optional["Layer"]:
    selection = viewer.layers.selection
    return next(iter(selection)) if len(selection) > 0 else None
