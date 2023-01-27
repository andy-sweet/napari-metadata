from napari.components import ViewerModel

from napari_metadata._axis_type_widget import AxesTypeWidget


def test_init(qtbot):
    viewer = ViewerModel()
    widget = AxesTypeWidget(None, viewer)
    qtbot.addWidget(widget)
