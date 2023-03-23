from typing import TYPE_CHECKING, List, Optional, Tuple

from qtpy.QtWidgets import QGridLayout, QLabel, QLineEdit, QWidget

from napari_metadata._widget_utils import (
    DoubleLineEdit,
    PositiveDoubleLineEdit,
    readonly_lineedit,
    set_row_visible,
    update_num_rows,
)

if TYPE_CHECKING:
    from napari.components import ViewerModel
    from napari.layers import Layer


class AxisTransformRow:
    def __init__(self) -> None:
        self.name = readonly_lineedit()
        self.spacing = PositiveDoubleLineEdit()
        self.spacing.setValue(1)
        self.translate = DoubleLineEdit()
        self.translate.setValue(0)

    def widgets(self) -> Tuple[QWidget, ...]:
        return (self.name, self.spacing, self.translate)


# TODO: reduce redundancy between this class and the AxesNameTypeWidget.
class AxesTransformWidget(QWidget):
    """Shows and controls all axes' names and spacing."""

    def __init__(self, viewer: "ViewerModel") -> None:
        super().__init__()
        self._viewer: "ViewerModel" = viewer
        self._layer: Optional["Layer"] = None
        self._rows: List[AxisTransformRow] = []
        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        layout.addWidget(QLabel("Name"), 0, 0)
        layout.addWidget(QLabel("Scale"), 0, 1)
        layout.addWidget(QLabel("Translate"), 0, 2)

        self.setLayout(layout)

        self._viewer.dims.events.axis_labels.connect(
            self._on_viewer_dims_axis_labels_changed
        )

    def set_selected_layer(self, layer: Optional["Layer"]) -> None:
        dims = self._viewer.dims
        update_num_rows(
            rows=self._rows,
            layout=self.layout(),
            desired_num=dims.ndim,
            row_factory=self._make_row,
        )

        self._set_axis_names(dims.axis_labels)
        layer_ndim = 0 if layer is None else layer.ndim
        ndim_diff = dims.ndim - layer_ndim
        for i, row in enumerate(self._axis_widgets()):
            set_row_visible(row, i >= ndim_diff)

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

    def _axis_widgets(self) -> Tuple[AxisTransformRow, ...]:
        return tuple(self._rows)

    def _layer_widgets(self) -> Tuple[AxisTransformRow, ...]:
        return (
            ()
            if self._layer is None
            else tuple(self._rows[-self._layer.ndim :])  # noqa
        )

    def _make_row(self) -> AxisTransformRow:
        widget = AxisTransformRow()
        widget.spacing.valueChanged.connect(self._on_pixel_size_changed)
        widget.translate.valueChanged.connect(self._on_translate_changed)
        return widget


class ReadOnlyAxisTransformRow:
    def __init__(self):
        self.name: QLineEdit = readonly_lineedit()
        self.spacing: QLineEdit = readonly_lineedit()
        self.translate: QLineEdit = readonly_lineedit()

    def widgets(self) -> Tuple[QWidget, ...]:
        return (self.name, self.spacing, self.translate)


class ReadOnlyAxesTransformWidget(QWidget):
    """Shows and controls all axes' transform parameters."""

    def __init__(self, viewer: "ViewerModel") -> None:
        super().__init__()
        self._viewer: "ViewerModel" = viewer
        self._layer: Optional["Layer"] = None
        self._rows: List[ReadOnlyAxisTransformRow] = []

        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        layout.addWidget(QLabel("Name"), 0, 0)
        layout.addWidget(QLabel("Scale"), 0, 1)
        layout.addWidget(QLabel("Translate"), 0, 2)

        self.setLayout(layout)

        self._viewer.dims.events.axis_labels.connect(
            self._on_viewer_dims_axis_labels_changed
        )

    def set_selected_layer(self, layer: Optional["Layer"]) -> None:
        dims = self._viewer.dims
        update_num_rows(
            rows=self._rows,
            layout=self.layout(),
            desired_num=dims.ndim,
            row_factory=ReadOnlyAxisTransformRow,
        )

        self._set_axis_names(dims.axis_labels)
        layer_ndim = 0 if layer is None else layer.ndim
        ndim_diff = dims.ndim - layer_ndim
        for i, row in enumerate(self._rows):
            set_row_visible(row, i >= ndim_diff)

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

    def _on_viewer_dims_axis_labels_changed(self) -> None:
        self._set_axis_names(self._viewer.dims.axis_labels)

    def _set_axis_names(self, names: Tuple[str, ...]) -> None:
        for name, row in zip(names, self._rows):
            row.name.setText(name)

    def _on_layer_scale_changed(self) -> None:
        assert self._layer is not None
        scale = self._layer.scale
        for s, r in zip(scale, self._layer_rows()):
            r.spacing.setText(str(s))

    def _on_layer_translate_changed(self) -> None:
        assert self._layer is not None
        translate = self._layer.translate
        for t, r in zip(translate, self._layer_rows()):
            r.translate.setText(str(t))

    def _layer_rows(self) -> Tuple[AxisTransformRow, ...]:
        return (
            ()
            if self._layer is None
            else tuple(self._rows[-self._layer.ndim :])  # noqa
        )
