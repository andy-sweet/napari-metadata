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
    get_layer_axis_names,
    get_layer_extra_metadata,
    set_layer_axis_names,
)

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

    def to_axis(self) -> Axis:
        axis_type = self.type.currentText()
        if axis_type == "channel":
            return ChannelAxis(name=self.name.text())
        elif axis_type == "time":
            return TimeAxis(name=self.name.text())
        return SpaceAxis(name=self.name.text())


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

        self.set_selected_layer(None)

    def set_selected_layer(self, layer: Optional["Layer"]) -> None:
        dims = self._viewer.dims
        self._update_num_axes(dims.ndim)
        if layer is not None:
            names = self._get_layer_axis_names(layer)
            # TODO: given the current we always need the event to be emitted,
            # to be sure that the widgets get some values, but this a giant
            # code smell.
            if dims.axis_labels == names:
                dims.events.axis_labels()
            else:
                dims.axis_labels = names
        layer_ndim = 0 if layer is None else layer.ndim
        ndim_diff = dims.ndim - layer_ndim
        for i, widget in enumerate(self.axis_widgets()):
            widget.setVisible(i >= ndim_diff)

    def _get_layer_axis_names(self, layer: "Layer") -> Tuple[str, ...]:
        viewer_names = list(self._viewer.dims.axis_labels)
        layer_names = get_layer_axis_names(layer)
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
        self._set_axis_names(self._viewer.dims.axis_labels)

    def _set_axis_names(self, names: Tuple[str, ...]) -> None:
        widgets = self.axis_widgets()
        assert len(names) == len(widgets)
        for name, widget in zip(names, widgets):
            widget.name.setText(name)
        for layer in self._viewer.layers:
            layer_axis_names = self._viewer.dims.axis_labels[
                -layer.ndim :  # noqa
            ]
            set_layer_axis_names(layer, layer_axis_names)

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
            if extras := get_layer_extra_metadata(layer):
                for i in range(layer.ndim):
                    extras.axes[i] = axis_widgets[
                        i + ndim - layer.ndim
                    ].to_axis()
