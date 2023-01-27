from typing import TYPE_CHECKING, List, Optional

from qtpy.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLayoutItem,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from napari_metadata._axis_type import AxisType

if TYPE_CHECKING:
    from napari.components import ViewerModel
    from napari.layers import Layer


class AxisTypeWidget(QWidget):
    def __init__(self, parent: Optional["QWidget"]) -> None:
        super().__init__(parent)
        self.setLayout(QHBoxLayout())
        self.name = QLineEdit()
        self.layout().addWidget(self.name)
        self.type = QComboBox()
        self.type.addItems(AxisType.names())
        self.layout().addWidget(self.type)


class AxesTypeWidget(QWidget):
    def __init__(
        self, parent: Optional["QWidget"], viewer: "ViewerModel"
    ) -> None:
        super().__init__(parent)
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Layer dimensions"))
        layout.setSpacing(2)
        self.setLayout(layout)
        # Need to reconsider if we want to support multiple viewers.
        viewer.dims.events.axis_labels.connect(
            self._on_viewer_dims_axis_labels_changed
        )
        self._layer: Optional["Layer"] = None
        self._viewer: "ViewerModel" = viewer
        self._update_num_axes(viewer.dims.ndim)
        self._set_axis_names(viewer.dims.axis_labels)

    def update(self, viewer: "ViewerModel", layer: "Layer") -> None:
        self._update_num_axes(viewer.dims.ndim)
        self._set_axis_names(viewer.dims.axis_labels)
        self._on_layer_changed(layer)

    def _on_layer_changed(self, layer: "Layer") -> None:
        self._layer = layer
        ndim_diff = self._viewer.dims.ndim - self._layer.ndim
        for i, widget in enumerate(self.axis_widgets()):
            widget.setEnabled(i >= ndim_diff)

    def connect_layer(self, layer: "Layer") -> None:
        pass

    def disconnect_layer(self, layer: "Layer") -> None:
        pass

    def _update_num_axes(self, num_axes: int) -> None:
        num_widgets: int = self.layout().count() - 1
        # Add any missing widgets.
        for _ in range(num_axes - num_widgets):
            widget = self._make_axis_widget()
            self.layout().addWidget(widget)
        # Remove any unneeded widgets.
        for i in range(num_widgets - num_axes):
            # +1 because first widget is label
            # TODO: better solution needed!
            item: QLayoutItem = self.layout().takeAt(num_widgets - i + 1)
            # Need to unparent? Instead of deleting?
            item.widget().deleteLater()

    def _make_axis_widget(self) -> None:
        widget = AxisTypeWidget(self)
        widget.name.textChanged.connect(self._on_axis_name_changed)
        return widget

    def _on_viewer_dims_axis_labels_changed(self, event) -> None:
        self._set_axis_names(event.value)

    def _set_axis_names(self, names: List[str]) -> None:
        widgets = self.axis_widgets()
        assert len(names) == len(widgets)
        for name, widget in zip(names, widgets):
            widget.name.setText(name)

    def axis_widgets(self) -> List[AxisTypeWidget]:
        # Implied cast from QLayoutItem to AxisWidget
        return [
            self.layout().itemAt(i).widget()
            for i in range(1, self.layout().count())
        ]

    def axis_names(self) -> List[str]:
        return [widget.name.text() for widget in self.axis_widgets()]

    def _on_axis_name_changed(self) -> None:
        self._viewer.dims.axis_labels = self.axis_names()
