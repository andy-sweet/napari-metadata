from typing import TYPE_CHECKING, List, Tuple

from qtpy.QtWidgets import QComboBox, QGridLayout, QLabel, QLineEdit, QWidget

from napari_metadata._axis_type import AxisType
from napari_metadata._model import (
    Axis,
    ChannelAxis,
    SpaceAxis,
    TimeAxis,
    extra_metadata,
)
from napari_metadata._space_units import SpaceUnits
from napari_metadata._time_units import TimeUnits
from napari_metadata._widget_utils import readonly_lineedit

if TYPE_CHECKING:
    from napari.components import ViewerModel
    from napari.layers import Layer


class AxisNameTypeWidget:
    """Contains one axis' name and type."""

    def __init__(self) -> None:
        self.name = QLineEdit()
        self.type = QComboBox()
        self.type.addItems(AxisType.names())

    def append_to_grid_layout(self, layout: QGridLayout) -> None:
        row = layout.count()
        layout.addWidget(self.name, row, 0)
        layout.addWidget(self.type, row, 1)

    def remove_from_grid_layout(self, layout: QGridLayout) -> None:
        for w in (self.name, self.type):
            layout.removeWidget(w)

    def setVisible(self, visible: bool) -> None:
        for w in (self.name, self.type):
            w.setVisible(visible)

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


class AxesNameTypeWidget(QWidget):
    """Shows and controls all axes' names and types."""

    def __init__(self, viewer: "ViewerModel") -> None:
        super().__init__()
        self._viewer: "ViewerModel" = viewer
        self._widgets: List[AxisNameTypeWidget] = []

        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(QLabel("Name"), 0, 0)
        layout.addWidget(QLabel("Type"), 0, 1)

        self.setLayout(layout)

        self._viewer.dims.events.axis_labels.connect(
            self._on_viewer_dims_axis_labels_changed
        )

    def set_selected_layer(self, layer: "Layer") -> None:
        dims = self._viewer.dims
        self._update_num_widgets(dims.ndim)

        names = self._get_layer_axis_names(layer)
        # TODO: given the current design we always need the event to be
        # emitted, to be sure that the widgets get some values, but this
        # a giant code smell.
        if dims.axis_labels == names:
            dims.events.axis_labels()
        else:
            dims.axis_labels = names
        ndim_diff = dims.ndim - layer.ndim

        extras = extra_metadata(layer)
        for i, widget in enumerate(self.axis_widgets()):
            widget.setVisible(i >= ndim_diff)
            if i >= ndim_diff:
                axis = extras.axes[i - ndim_diff]
                widget.type.setCurrentText(str(axis.get_type()))

    def _update_num_widgets(self, desired_num: int) -> None:
        current_num = len(self._widgets)
        # Add any missing widgets.
        for _ in range(desired_num - current_num):
            widget = self._make_axis_widget()
            widget.append_to_grid_layout(self.layout())
            self._widgets.append(widget)
        # Remove any unneeded widgets.
        for _ in range(current_num - 1, desired_num - 1, -1):
            widget = self._widgets.pop()
            widget.remove_from_grid_layout(self.layout())

    def _get_layer_axis_names(self, layer: "Layer") -> Tuple[str, ...]:
        viewer_names = list(self._viewer.dims.axis_labels)
        layer_names = extra_metadata(layer).get_axis_names()
        viewer_names[-layer.ndim :] = layer_names  # noqa
        return tuple(viewer_names)

    def _make_axis_widget(self) -> AxisNameTypeWidget:
        widget = AxisNameTypeWidget()
        widget.name.textChanged.connect(self._on_axis_name_changed)
        widget.type.currentTextChanged.connect(self._on_axis_type_changed)
        return widget

    def _on_viewer_dims_axis_labels_changed(self) -> None:
        widgets = self.axis_widgets()
        names = self._viewer.dims.axis_labels
        assert len(names) == len(widgets)
        for name, widget in zip(names, widgets):
            widget.name.setText(name)
        for layer in self._viewer.layers:
            if extras := extra_metadata(layer):
                axis_names = self._viewer.dims.axis_labels[
                    -layer.ndim :  # noqa
                ]
                extras.set_axis_names(axis_names)

    def axis_widgets(self) -> Tuple[AxisNameTypeWidget, ...]:
        return tuple(self._widgets)

    def axis_names(self) -> Tuple[str, ...]:
        return tuple(widget.name.text() for widget in self.axis_widgets())

    def _on_axis_name_changed(self) -> None:
        self._viewer.dims.axis_labels = self.axis_names()

    def _on_axis_type_changed(self) -> None:
        axis_widgets = self.axis_widgets()
        ndim = len(axis_widgets)
        for layer in self._viewer.layers:
            extras = extra_metadata(layer)
            space_unit = extras.get_space_unit()
            time_unit = extras.get_time_unit()
            for i in range(layer.ndim):
                widget = axis_widgets[i + ndim - layer.ndim]
                extras.axes[i] = widget.to_axis(
                    space_unit=space_unit,
                    time_unit=time_unit,
                )


class ReadOnlyAxisNameTypeWidgets:
    """Contains one axis' name and type."""

    def __init__(self) -> None:
        self.name = readonly_lineedit()
        self.type = readonly_lineedit()

    def append_to_grid_layout(self, layout: QGridLayout) -> None:
        row = layout.count()
        layout.addWidget(self.name, row, 0)
        layout.addWidget(self.type, row, 1)

    def remove_from_grid_layout(self, layout: QGridLayout) -> None:
        for w in (self.name, self.type):
            layout.removeWidget(w)

    def setVisible(self, visible: bool) -> None:
        for w in (self.name, self.type):
            w.setVisible(visible)


class ReadOnlyAxesNameTypeWidget(QWidget):
    """Shows all axes' names and types."""

    def __init__(self, viewer: "ViewerModel") -> None:
        super().__init__()
        self._viewer: "ViewerModel" = viewer
        self._widgets: List[ReadOnlyAxisNameTypeWidgets] = []

        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel("Name"), 0, 0)
        layout.addWidget(QLabel("Type"), 0, 1)
        self.setLayout(layout)

        self._viewer.dims.events.axis_labels.connect(
            self._on_viewer_dims_axis_labels_changed
        )

    def set_selected_layer(self, layer: "Layer") -> None:
        dims = self._viewer.dims
        self._update_num_widgets(dims.ndim)
        ndim_diff = dims.ndim - layer.ndim
        extras = extra_metadata(layer)
        for i, widget in enumerate(self._axis_widgets()):
            widget.setVisible(i >= ndim_diff)
            if i >= ndim_diff:
                axis = extras.axes[i - ndim_diff]
                widget.name.setText(axis.name)
                widget.type.setText(str(axis.get_type()))

    def _update_num_widgets(self, desired_num: int) -> None:
        current_num = len(self._widgets)
        # Add any missing widgets.
        for _ in range(desired_num - current_num):
            widget = ReadOnlyAxisNameTypeWidgets()
            widget.append_to_grid_layout(self.layout())
            self._widgets.append(widget)
        # Remove any unneeded widgets.
        for _ in range(current_num - 1, desired_num - 1, -1):
            widget = self._widgets.pop()
            widget.remove_from_grid_layout(self.layout())

    def _on_viewer_dims_axis_labels_changed(self) -> None:
        self._set_axis_names(self._viewer.dims.axis_labels)

    def _set_axis_names(self, names: Tuple[str, ...]) -> None:
        widgets = self._axis_widgets()
        names = self._viewer.dims.axis_labels
        assert len(names) == len(widgets)
        for name, widget in zip(names, widgets):
            widget.name.setText(name)

    def _axis_widgets(self) -> Tuple[AxisNameTypeWidget, ...]:
        return tuple(self._widgets)
