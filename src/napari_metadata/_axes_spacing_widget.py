from typing import TYPE_CHECKING, List, Optional, Tuple, cast

from qtpy.QtWidgets import (
    QAbstractSpinBox,
    QDoubleSpinBox,
    QGridLayout,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)

from napari_metadata._widget_utils import readonly_lineedit, update_num_widgets

if TYPE_CHECKING:
    from napari.components import ViewerModel
    from napari.layers import Layer


def make_double_spinbox(value: float, *, lower: float) -> QDoubleSpinBox:
    spinbox = QDoubleSpinBox()
    spinbox.setDecimals(6)
    spinbox.setMinimum(lower)
    spinbox.setValue(value)
    spinbox.setSingleStep(0.1)
    spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
    return spinbox


class AxisTransformWidgets:
    """Contains one axis' name, scale, and translate widgets."""

    def __init__(self) -> None:
        self.name = readonly_lineedit()
        self.spacing = make_double_spinbox(1, lower=1e-6)
        self.translate = make_double_spinbox(0, lower=-1e6)

    def append_to_grid_layout(self, layout: QGridLayout) -> None:
        row = layout.count()
        layout.addWidget(self.name, row, 0)
        layout.addWidget(self.spacing, row, 1)
        layout.addWidget(self.translate, row, 2)

    def remove_from_grid_layout(self, layout: QGridLayout) -> None:
        for w in (self.name, self.spacing, self.translate):
            layout.removeWidget(w)

    def setVisible(self, visible: bool) -> None:
        for w in (self.name, self.spacing, self.translate):
            w.setVisible(visible)


# TODO: reduce redundancy between this class and the AxesNameTypeWidget.
class AxesSpacingWidget(QWidget):
    """Shows and controls all axes' names and spacing."""

    def __init__(self, viewer: "ViewerModel") -> None:
        super().__init__()
        self._viewer: "ViewerModel" = viewer
        self._layer: Optional["Layer"] = None
        self._widgets: List[AxisTransformWidgets] = []
        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        layout.addWidget(readonly_lineedit(), 0, 0)
        layout.addWidget(readonly_lineedit("Scale"), 0, 1)
        layout.addWidget(readonly_lineedit("Translate"), 0, 2)

        self.setLayout(layout)

        self._viewer.dims.events.axis_labels.connect(
            self._on_viewer_dims_axis_labels_changed
        )

    def set_selected_layer(self, layer: Optional["Layer"]) -> None:
        dims = self._viewer.dims
        self._update_num_widgets(dims.ndim)

        self._set_axis_names(dims.axis_labels)
        layer_ndim = 0 if layer is None else layer.ndim
        ndim_diff = dims.ndim - layer_ndim
        for i, widget in enumerate(self._axis_widgets()):
            widget.setVisible(i >= ndim_diff)

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

    def _update_num_widgets(self, desired_num: int) -> None:
        current_num = len(self._widgets)
        # Add any missing widgets.
        for _ in range(desired_num - current_num):
            widget = self._make_axis_transform_widgets()
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
        for name, widget in zip(names, widgets):
            widget.name.setText(name)

    def _on_layer_scale_changed(self) -> None:
        assert self._layer is not None
        scale = self._layer.scale
        widgets = self._layer_widgets()
        for s, w in zip(scale, widgets):
            w.spacing.setValue(s)

    def _on_layer_translate_changed(self) -> None:
        assert self._layer is not None
        translate = self._layer.translate
        widgets = self._layer_widgets()
        for t, w in zip(translate, widgets):
            w.translate.setValue(t)

    def _on_pixel_size_changed(self) -> None:
        scale = tuple(w.spacing.value() for w in self._layer_widgets())
        self._layer.scale = scale

    def _on_translate_changed(self) -> None:
        translate = tuple(w.translate.value() for w in self._layer_widgets())
        self._layer.translate = translate

    def _axis_widgets(self) -> Tuple[AxisTransformWidgets, ...]:
        return tuple(self._widgets)

    def _layer_widgets(self) -> Tuple[AxisTransformWidgets, ...]:
        return (
            ()
            if self._layer is None
            else tuple(self._widgets[-self._layer.ndim :])  # noqa
        )

    def _make_axis_transform_widgets(self) -> AxisTransformWidgets:
        widget = AxisTransformWidgets()
        widget.spacing.valueChanged.connect(self._on_pixel_size_changed)
        widget.translate.valueChanged.connect(self._on_translate_changed)
        return widget


class ReadOnlyAxisSpacingWidget(QWidget):
    """Shows one axis' name and spacing."""

    def __init__(self, parent: Optional["QWidget"]) -> None:
        super().__init__(parent)
        self.name = readonly_lineedit()
        self.spacing = readonly_lineedit()

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
        update_num_widgets(
            layout=self.layout(),
            desired_num=dims.ndim,
            widget_factory=lambda: ReadOnlyAxisSpacingWidget(self),
        )

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
        layer_ndim = 0 if self._layer is None else self._layer.ndim
        ndim_diff = self._viewer.dims.ndim - layer_ndim
        layer_widgets = []
        for i, widget in enumerate(self._axis_widgets()):
            if i >= ndim_diff:
                layer_widgets.append(widget)
        return tuple(layer_widgets)
