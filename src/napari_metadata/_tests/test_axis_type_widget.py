from napari.components import ViewerModel
from qtpy.QtWidgets import QWidget

from napari_metadata._axis_type_widget import AxesTypeWidget


def test_init_with_no_layers(qtbot):
    viewer = ViewerModel()
    assert viewer.layers.selection == set()

    widget = make_axes_type_widget(qtbot, viewer)

    assert widget.axis_names() == ["0", "1"]
    assert sum(map(QWidget.isEnabled, widget.axis_widgets())) == 2


def make_axes_type_widget(qtbot, viewer) -> AxesTypeWidget:
    widget = AxesTypeWidget(viewer)
    qtbot.addWidget(widget)
    return widget
