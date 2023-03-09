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


class AxisNameTypeWidget(QWidget):
    """Shows and controls one axis' name and type."""

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

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self._viewer.dims.events.axis_labels.connect(
            self._on_viewer_dims_axis_labels_changed
        )

    def set_selected_layer(self, layer: "Layer") -> None:
        dims = self._viewer.dims
        self._update_num_axes(dims.ndim)

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

    def _get_layer_axis_names(self, layer: "Layer") -> Tuple[str, ...]:
        viewer_names = list(self._viewer.dims.axis_labels)
        layer_names = extra_metadata(layer).get_axis_names()
        viewer_names[-layer.ndim :] = layer_names  # noqa
        return tuple(viewer_names)

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

    def _make_axis_widget(self) -> AxisNameTypeWidget:
        widget = AxisNameTypeWidget(self)
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
        layout = self.layout()
        return [
            cast(AxisNameTypeWidget, layout.itemAt(i).widget())
            for i in range(0, layout.count())
        ]

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


class ReadOnlyAxisNameTypeWidget(QWidget):
    """Shows one axis' name and type."""

    def __init__(self, parent: Optional["QWidget"]) -> None:
        super().__init__(parent)
        self.name = readonly_lineedit()
        self.type = readonly_lineedit()

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.name)
        layout.addWidget(self.type)
        self.setLayout(layout)


class ReadOnlyAxesNameTypeWidget(QWidget):
    """Shows all axes' names and types."""

    def __init__(self, viewer: "ViewerModel") -> None:
        super().__init__()
        self._viewer: "ViewerModel" = viewer

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self._viewer.dims.events.axis_labels.connect(
            self._on_viewer_dims_axis_labels_changed
        )

    def set_selected_layer(self, layer: "Layer") -> None:
        dims = self._viewer.dims
        self._update_num_axes(dims.ndim)
        ndim_diff = dims.ndim - layer.ndim
        extras = extra_metadata(layer)
        for i, widget in enumerate(self._axis_widgets()):
            widget.setVisible(i >= ndim_diff)
            if i >= ndim_diff:
                axis = extras.axes[i - ndim_diff]
                widget.name.setText(axis.name)
                widget.type.setText(str(axis.get_type()))

    def _update_num_axes(self, num_axes: int) -> None:
        num_widgets: int = self.layout().count()
        # Add any missing widgets.
        for _ in range(num_axes - num_widgets):
            widget = ReadOnlyAxisNameTypeWidget(self)
            self.layout().addWidget(widget)
        # Remove any unneeded widgets.
        for i in range(num_widgets - num_axes):
            item: QLayoutItem = self.layout().takeAt(num_widgets - (i + 1))
            item.widget().deleteLater()

    def _on_viewer_dims_axis_labels_changed(self) -> None:
        self._set_axis_names(self._viewer.dims.axis_labels)

    def _set_axis_names(self, names: Tuple[str, ...]) -> None:
        widgets = self._axis_widgets()
        names = self._viewer.dims.axis_labels
        assert len(names) == len(widgets)
        for name, widget in zip(names, widgets):
            widget.name.setText(name)

    def _axis_widgets(self) -> Tuple[ReadOnlyAxisNameTypeWidget, ...]:
        layout = self.layout()
        return tuple(
            cast(ReadOnlyAxisNameTypeWidget, layout.itemAt(i).widget())
            for i in range(0, layout.count())
        )
