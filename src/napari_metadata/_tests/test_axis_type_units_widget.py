from napari.components import ViewerModel

from napari_metadata._axis_type_units_widget import AxesTypeUnitsWidget


def test_init(qtbot):
    viewer = ViewerModel()
    widget = AxesTypeUnitsWidget(None, viewer)
    qtbot.addWidget(widget)
