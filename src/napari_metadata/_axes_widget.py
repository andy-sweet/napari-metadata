from typing import TYPE_CHECKING, List, Optional, Tuple

from qtpy.QtWidgets import QComboBox, QGridLayout, QLabel, QLineEdit, QWidget

from napari_metadata._axis_type import AxisType
from napari_metadata._model import (
    Axis,
    ChannelAxis,
    SpaceAxis,
    TimeAxis,
    coerce_extra_metadata,
)
from napari_metadata._space_units import SpaceUnits
from napari_metadata._time_units import TimeUnits
from napari_metadata._widget_utils import (
    CompactLineEdit,
    DoubleLineEdit,
    readonly_lineedit,
    set_row_visible,
    update_num_rows,
)

if TYPE_CHECKING:
    from napari.components import ViewerModel
    from napari.layers import Layer


class AxisRow:
    def __init__(self) -> None:
        self.name: QLineEdit = CompactLineEdit()
        self.type: QComboBox = QComboBox()
        self.type.addItems(AxisType.names())
        self.scale = DoubleLineEdit()
        self.scale.setValue(1)
        self.translate = DoubleLineEdit()
        self.translate.setValue(0)

    def widgets(self) -> Tuple[QWidget, ...]:
        return (self.name, self.type, self.scale, self.translate)

    def to_axis(
        self,
        *,
        space_unit: SpaceUnits = SpaceUnits.NONE,
        time_unit: TimeUnits = TimeUnits.NONE,
    ) -> Axis:
        axis_type = self.type.currentText()
        if axis_type == "channel":
            return ChannelAxis(name=self.name.text())
        elif axis_type == "time":
            return TimeAxis(name=self.name.text(), unit=time_unit)
        return SpaceAxis(name=self.name.text(), unit=space_unit)


class AxesWidget(QWidget):
    """Shows and controls all axes' names and types."""

    def __init__(self, viewer: "ViewerModel") -> None:
        super().__init__()
        self._viewer: "ViewerModel" = viewer
        self._layer: Optional["Layer"] = None
        self._rows: List[AxisRow] = []

        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(QLabel("Name"), 0, 0)
        layout.addWidget(QLabel("Type"), 0, 1)
        layout.addWidget(QLabel("Scale"), 0, 2)
        layout.addWidget(QLabel("Translate"), 0, 3)

        self.setLayout(layout)

        self._viewer.dims.events.axis_labels.connect(
            self._on_viewer_dims_axis_labels_changed
        )

    def set_selected_layer(self, layer: "Layer") -> None:
        dims = self._viewer.dims
        update_num_rows(
            rows=self._rows,
            layout=self.layout(),
            desired_num=dims.ndim,
            row_factory=self._make_row,
        )

        names = self._get_layer_axis_names(layer)
        # TODO: given the current design we always need the event to be
        # emitted, to be sure that the widgets get some values, but this
        # a giant code smell.
        if dims.axis_labels == names:
            dims.events.axis_labels()
        else:
            dims.axis_labels = names
        ndim_diff = dims.ndim - layer.ndim

        old_layer = self._layer
        if old_layer is not None:
            old_layer.events.scale.disconnect(self._on_layer_scale_changed)
            old_layer.events.translate.disconnect(
                self._on_layer_translate_changed
            )
        if layer is not None:
            layer.events.scale.connect(self._on_layer_scale_changed)
            layer.events.translate.connect(self._on_layer_translate_changed)
        self._layer = layer
        if self._layer is not None:
            self._on_layer_scale_changed()
            self._on_layer_translate_changed()

        extras = coerce_extra_metadata(self._viewer, layer)
        for i, row in enumerate(self._rows):
            set_row_visible(row, i >= ndim_diff)
            if i >= ndim_diff:
                axis = extras.axes[i - ndim_diff]
                row.type.setCurrentText(str(axis.get_type()))

    def _get_layer_axis_names(self, layer: "Layer") -> Tuple[str, ...]:
        viewer_names = list(self._viewer.dims.axis_labels)
        extras = coerce_extra_metadata(self._viewer, layer)
        layer_names = extras.get_axis_names()
        viewer_names[-layer.ndim :] = layer_names  # noqa
        return tuple(viewer_names)

    def _make_row(self) -> AxisRow:
        widget = AxisRow()
        widget.name.textChanged.connect(self._on_axis_name_changed)
        widget.type.currentTextChanged.connect(self._on_axis_type_changed)
        widget.scale.valueChanged.connect(self._on_pixel_size_changed)
        widget.translate.valueChanged.connect(self._on_translate_changed)
        return widget

    def _on_viewer_dims_axis_labels_changed(self) -> None:
        names = self._viewer.dims.axis_labels
        assert len(names) == len(self._rows)
        for name, row in zip(names, self._rows):
            row.name.setText(name)
        for layer in self._viewer.layers:
            extras = coerce_extra_metadata(self._viewer, layer)
            axis_names = self._viewer.dims.axis_labels[-layer.ndim :]  # noqa
            extras.set_axis_names(axis_names)

    def _on_layer_scale_changed(self) -> None:
        assert self._layer is not None
        scale = self._layer.scale
        widgets = self._layer_widgets()
        for s, w in zip(scale, widgets):
            w.scale.setValue(s)

    def _on_layer_translate_changed(self) -> None:
        assert self._layer is not None
        translate = self._layer.translate
        widgets = self._layer_widgets()
        for t, w in zip(translate, widgets):
            w.translate.setValue(t)

    def _on_pixel_size_changed(self) -> None:
        scale = tuple(w.scale.value() for w in self._layer_widgets())
        self._layer.scale = scale

    def _on_translate_changed(self) -> None:
        translate = tuple(w.translate.value() for w in self._layer_widgets())
        self._layer.translate = translate

    def axis_widgets(self) -> Tuple[AxisRow, ...]:
        return tuple(self._rows)

    def _layer_widgets(self) -> Tuple[AxisRow, ...]:
        return (
            ()
            if self._layer is None
            else tuple(self._rows[-self._layer.ndim :])  # noqa
        )

    def axis_names(self) -> Tuple[str, ...]:
        return tuple(widget.name.text() for widget in self.axis_widgets())

    def _on_axis_name_changed(self) -> None:
        self._viewer.dims.axis_labels = self.axis_names()

    def _on_axis_type_changed(self) -> None:
        axis_widgets = self.axis_widgets()
        ndim = len(axis_widgets)
        for layer in self._viewer.layers:
            extras = coerce_extra_metadata(self._viewer, layer)
            space_unit = extras.get_space_unit()
            time_unit = extras.get_time_unit()
            for i in range(layer.ndim):
                widget = axis_widgets[i + ndim - layer.ndim]
                extras.axes[i] = widget.to_axis(
                    space_unit=space_unit,
                    time_unit=time_unit,
                )


class ReadOnlyAxisRow:
    def __init__(self) -> None:
        self.name: QLineEdit = readonly_lineedit()
        self.type: QLineEdit = readonly_lineedit()
        self.scale: QLineEdit = readonly_lineedit()
        self.translate: QLineEdit = readonly_lineedit()

    def widgets(self) -> Tuple[QWidget, ...]:
        return (self.name, self.type, self.scale, self.translate)


class ReadOnlyAxesWidget(QWidget):
    """Shows all axes' names and types."""

    def __init__(self, viewer: "ViewerModel") -> None:
        super().__init__()
        self._viewer: "ViewerModel" = viewer
        self._layer: Optional["Layer"] = None
        self._rows: List[ReadOnlyAxisRow] = []

        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel("Name"), 0, 0)
        layout.addWidget(QLabel("Type"), 0, 1)
        layout.addWidget(QLabel("Scale"), 0, 2)
        layout.addWidget(QLabel("Translate"), 0, 3)
        self.setLayout(layout)

        self._viewer.dims.events.axis_labels.connect(
            self._on_viewer_dims_axis_labels_changed
        )

    def set_selected_layer(self, layer: "Layer") -> None:
        dims = self._viewer.dims
        update_num_rows(
            rows=self._rows,
            layout=self.layout(),
            desired_num=dims.ndim,
            row_factory=ReadOnlyAxisRow,
        )
        ndim_diff = dims.ndim - layer.ndim
        extras = coerce_extra_metadata(self._viewer, layer)
        for i, row in enumerate(self._rows):
            set_row_visible(row, i >= ndim_diff)
            if i >= ndim_diff:
                axis = extras.axes[i - ndim_diff]
                row.name.setText(axis.name)
                row.type.setText(str(axis.get_type()))

        old_layer = self._layer
        if old_layer is not None:
            old_layer.events.scale.disconnect(self._on_layer_scale_changed)
            old_layer.events.translate.disconnect(
                self._on_layer_translate_changed
            )
        if layer is not None:
            layer.events.scale.connect(self._on_layer_scale_changed)
            layer.events.translate.connect(self._on_layer_translate_changed)
        self._layer = layer
        if self._layer is not None:
            self._on_layer_scale_changed()
            self._on_layer_translate_changed()

    def _on_layer_scale_changed(self) -> None:
        assert self._layer is not None
        scale = self._layer.scale
        for s, r in zip(scale, self._layer_rows()):
            r.scale.setText(str(s))

    def _on_layer_translate_changed(self) -> None:
        assert self._layer is not None
        translate = self._layer.translate
        for t, r in zip(translate, self._layer_rows()):
            r.translate.setText(str(t))

    def _layer_rows(self) -> Tuple[ReadOnlyAxisRow, ...]:
        return (
            ()
            if self._layer is None
            else tuple(self._rows[-self._layer.ndim :])  # noqa
        )

    def _on_viewer_dims_axis_labels_changed(self) -> None:
        self._set_axis_names(self._viewer.dims.axis_labels)

    def _set_axis_names(self, names: Tuple[str, ...]) -> None:
        names = self._viewer.dims.axis_labels
        assert len(names) == len(self._rows)
        for name, widget in zip(names, self._rows):
            widget.name.setText(name)
