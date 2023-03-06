from typing import TYPE_CHECKING, Optional, Tuple, cast

from qtpy.QtWidgets import (
    QAbstractSpinBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QLayoutItem,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from napari.components import ViewerModel
    from napari.layers import Layer


class AxisSpacingWidget(QWidget):
    """Shows and controls one axis' name and spacing."""

    def __init__(self, parent: Optional["QWidget"]) -> None:
        super().__init__(parent)
        self.name = QLabel()
        self.spacing = QDoubleSpinBox()
        self.spacing.setDecimals(6)
        self.spacing.setRange(1e-6, 1e6)
        self.spacing.setValue(1)
        self.spacing.setStepType(
            QAbstractSpinBox.StepType.AdaptiveDecimalStepType
        )

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.name)
        layout.addWidget(self.spacing)
        self.setLayout(layout)


# TODO: reduce redundancy between this class and the AxesNameTypeWidget.
class AxesSpacingWidget(QWidget):
    """Shows and controls all axes' names and spacing."""

    def __init__(self, viewer: "ViewerModel") -> None:
        super().__init__()
        self._viewer: "ViewerModel" = viewer
        self._layer: Optional["Layer"] = None
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self._viewer.dims.events.axis_labels.connect(
            self._on_viewer_dims_axis_labels_changed
        )

    def set_selected_layer(self, layer: Optional["Layer"]) -> None:
        dims = self._viewer.dims
        self._update_num_axes(dims.ndim)
        self._set_axis_names(dims.axis_labels)
        layer_ndim = 0 if layer is None else layer.ndim
        ndim_diff = dims.ndim - layer_ndim
        for i, widget in enumerate(self._axis_widgets()):
            widget.setVisible(i >= ndim_diff)

        old_layer = self._layer
        if old_layer is not None:
            old_layer.events.scale.disconnect(self._on_layer_scale_changed)
        if layer is not None:
            layer.events.scale.connect(self._on_layer_scale_changed)
        self._layer = layer
        if self._layer is not None:
            self._on_layer_scale_changed()

    def _on_viewer_dims_axis_labels_changed(self) -> None:
        self._set_axis_names(self._viewer.dims.axis_labels)

    def _set_axis_names(self, names: Tuple[str, ...]) -> None:
        widgets = self._axis_widgets()
        for name, widget in zip(names, widgets):
            widget.name.setText(name)

    def _on_layer_scale_changed(self) -> None:
        assert self._layer is not None
        scale = self._layer.scale
        widgets = self._layer_widgets()
        for s, w in zip(scale, widgets):
            w.spacing.setValue(s)

    def _on_pixel_size_changed(self) -> None:
        scale = tuple(w.spacing.value() for w in self._layer_widgets())
        self._layer.scale = scale

    def _axis_widgets(self) -> Tuple[AxisSpacingWidget, ...]:
        layout = self.layout()
        return [
            cast(AxisSpacingWidget, layout.itemAt(i).widget())
            for i in range(0, layout.count())
        ]

    def _layer_widgets(self) -> Tuple[AxisSpacingWidget, ...]:
        layer = self._layer
        dims = self._viewer.dims
        layer_ndim = 0 if layer is None else layer.ndim
        ndim_diff = dims.ndim - layer_ndim
        layer_widgets = []
        for i, widget in enumerate(self._axis_widgets()):
            if i >= ndim_diff:
                layer_widgets.append(widget)
        return tuple(layer_widgets)

    def _update_num_axes(self, num_axes: int) -> None:
        num_widgets: int = self.layout().count()
        # Add any missing widgets.
        for _ in range(num_axes - num_widgets):
            widget = self._make_axis_spacing_widget()
            self.layout().addWidget(widget)
        # Remove any unneeded widgets.
        for i in range(num_widgets - num_axes):
            item: QLayoutItem = self.layout().takeAt(num_widgets - (i + 1))
            item.widget().deleteLater()

    def _make_axis_spacing_widget(self) -> AxisSpacingWidget:
        widget = AxisSpacingWidget(self)
        widget.spacing.valueChanged.connect(self._on_pixel_size_changed)
        return widget


class ReadOnlyAxisSpacingWidget(QWidget):
    """Shows one axis' name and spacing."""

    def __init__(self, parent: Optional["QWidget"]) -> None:
        super().__init__(parent)
        self.name = QLabel()
        self.spacing = QLabel()

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.name)
        layout.addWidget(self.spacing)
        self.setLayout(layout)


class ReadOnlyAxesSpacingWidget(QWidget):
    """Shows and controls all axes' names and spacing."""

    def __init__(self, viewer: "ViewerModel") -> None:
        super().__init__()
        self._viewer: "ViewerModel" = viewer
        self._layer: Optional["Layer"] = None
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self._viewer.dims.events.axis_labels.connect(
            self._on_viewer_dims_axis_labels_changed
        )

    def set_selected_layer(self, layer: Optional["Layer"]) -> None:
        dims = self._viewer.dims
        self._update_num_axes(dims.ndim)
        self._set_axis_names(dims.axis_labels)
        layer_ndim = 0 if layer is None else layer.ndim
        ndim_diff = dims.ndim - layer_ndim
        for i, widget in enumerate(self._axis_widgets()):
            widget.setVisible(i >= ndim_diff)

        old_layer = self._layer
        if old_layer is not None:
            old_layer.events.scale.disconnect(self._on_layer_scale_changed)
        if layer is not None:
            layer.events.scale.connect(self._on_layer_scale_changed)
        self._layer = layer
        if self._layer is not None:
            self._on_layer_scale_changed()

    def _on_viewer_dims_axis_labels_changed(self) -> None:
        self._set_axis_names(self._viewer.dims.axis_labels)

    def _set_axis_names(self, names: Tuple[str, ...]) -> None:
        widgets = self._axis_widgets()
        for name, widget in zip(names, widgets):
            widget.name.setText(name)

    def _on_layer_scale_changed(self) -> None:
        assert self._layer is not None
        scale = self._layer.scale
        widgets = self._layer_widgets()
        for s, w in zip(scale, widgets):
            w.spacing.setText(str(s))

    def _axis_widgets(self) -> Tuple[ReadOnlyAxisSpacingWidget, ...]:
        layout = self.layout()
        return [
            cast(ReadOnlyAxisSpacingWidget, layout.itemAt(i).widget())
            for i in range(0, layout.count())
        ]

    def _layer_widgets(self) -> Tuple[ReadOnlyAxisSpacingWidget, ...]:
        layer = self._layer
        dims = self._viewer.dims
        layer_ndim = 0 if layer is None else layer.ndim
        ndim_diff = dims.ndim - layer_ndim
        layer_widgets = []
        for i, widget in enumerate(self._axis_widgets()):
            if i >= ndim_diff:
                layer_widgets.append(widget)
        return tuple(layer_widgets)

    def _update_num_axes(self, num_axes: int) -> None:
        num_widgets: int = self.layout().count()
        # Add any missing widgets.
        for _ in range(num_axes - num_widgets):
            widget = ReadOnlyAxisSpacingWidget(self)
            self.layout().addWidget(widget)
        # Remove any unneeded widgets.
        for i in range(num_widgets - num_axes):
            item: QLayoutItem = self.layout().takeAt(num_widgets - (i + 1))
            item.widget().deleteLater()
