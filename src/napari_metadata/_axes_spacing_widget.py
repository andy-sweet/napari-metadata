from typing import TYPE_CHECKING, Optional, Tuple, cast

from qtpy.QtWidgets import (
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QLayoutItem,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from napari.layers import Layer


class AxisSpacingWidget(QWidget):
    """Shows and controls one axis' name and spacing."""

    def __init__(self, parent: Optional["QWidget"]) -> None:
        super().__init__(parent)
        self.name = QLabel()
        self.spacing = QDoubleSpinBox()
        self.spacing.setValue(1)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.name)
        layout.addWidget(self.spacing)
        self.setLayout(layout)


class AxesSpacingWidget(QWidget):
    """Shows and controls all axes' names and spacing."""

    def __init__(self) -> None:
        super().__init__()
        self._layer: Optional["Layer"] = None
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def set_selected_layer(self, layer: Optional["Layer"]) -> None:
        layer_ndim = 0 if layer is None else layer.ndim
        self._update_num_axes(layer_ndim)
        old_layer = self._layer
        if old_layer is not None:
            old_layer.events.scale.disconnect(self._on_layer_scale_changed)
        if layer is not None:
            layer.events.scale.connect(self._on_layer_scale_changed)
        self._layer = layer
        if self._layer is not None:
            self._on_layer_scale_changed()

    def set_axis_names(self, names: Tuple[str, ...]) -> None:
        widgets = self._axis_widgets()
        assert len(names) == len(widgets)
        for i, widget in enumerate(self._axis_widgets()):
            widget.name.setText(names[i])

    def set_axis_units(self, units: Tuple[str, ...]) -> None:
        widgets = self._axis_widgets()
        assert len(units) == len(widgets)
        for i, widget in enumerate(self._axis_widgets()):
            widget.spacing.setSuffix(" " + units[i])

    def _on_layer_scale_changed(self) -> None:
        assert self._layer is not None
        scale = self._layer.scale
        widgets = self._axis_widgets()
        assert len(scale) == len(widgets)
        for i, widget in enumerate(widgets):
            widget.spacing.setValue(scale[i])

    def _on_pixel_size_changed(self) -> None:
        widgets = self._axis_widgets()
        scale = tuple(w.spacing.value() for w in widgets)
        self._layer.scale = scale

    def _axis_widgets(self) -> Tuple[AxisSpacingWidget, ...]:
        layout = self.layout()
        return [
            cast(AxisSpacingWidget, layout.itemAt(i).widget())
            for i in range(0, layout.count())
        ]

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
