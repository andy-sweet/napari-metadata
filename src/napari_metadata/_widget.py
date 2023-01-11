from typing import TYPE_CHECKING

from magicgui import magic_factory
from qtpy.QtWidgets import (
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    import napari


class ExampleQWidget(QWidget):
    def __init__(self, viewer: "napari.viewer.Viewer"):
        super().__init__()
        self._value_edits = {}
        self._restore_buttons = {}
        self.viewer = viewer
        self.viewer.layers.selection.events.changed.connect(
            self._on_selected_layers_changed
        )

        layout = QVBoxLayout()
        self.setLayout(layout)

        description = QLabel(
            "View and edit metadata values, and select which to display in GUI"
        )
        layout.addWidget(description)

        self._attribute_widget = QWidget()
        layout.addWidget(self._attribute_widget)

        self._attribute_layout = QGridLayout()
        self._attribute_widget.setLayout(self._attribute_layout)
        self._add_attribute_widgets("name")
        self._add_attribute_widgets("scale", editable=True)

        self._on_selected_layers_changed()

    def _add_attribute_widgets(
        self, name: str, *, editable: bool = False
    ) -> None:
        restore_button = QPushButton("Restore")
        value_edit = QLineEdit("")
        value_edit.setEnabled(editable)
        layout = self._attribute_widget.layout()
        row = layout.rowCount()
        layout.addWidget(QLabel(name), row, 0)
        layout.addWidget(value_edit, row, 1)
        layout.addWidget(restore_button, row, 2)
        self._value_edits[name] = value_edit
        self._restore_buttons[name] = restore_button

    def _on_selected_layers_changed(self) -> None:
        if len(self.viewer.layers.selection) == 1:
            self._show_selected_attributes()
        else:
            self._hide_attributes()

    def _show_selected_attributes(self) -> None:
        self._attribute_widget.show()
        layer = next(iter(self.viewer.layers.selection))
        for name in self._value_edits:
            value = getattr(layer, name)
            self._value_edits[name].setText(str(value))

    def _hide_attributes(self) -> None:
        self._attribute_widget.hide()


@magic_factory
def example_magic_widget(img_layer: "napari.layers.Image"):
    print(f"you have selected {img_layer}")


# Uses the `autogenerate: true` flag in the plugin manifest
# to indicate it should be wrapped as a magicgui to autogenerate
# a widget.
def example_function_widget(img_layer: "napari.layers.Image"):
    print(f"you have selected {img_layer}")
