import numpy as np
from napari.components import ViewerModel
from qtpy.QtWidgets import QWidget

from napari_metadata import QMetadataWidget


def test_init_with_no_layers(qtbot):
    viewer = ViewerModel()
    assert viewer.layers.selection == set()

    widget = make_metadata_widget(qtbot, viewer)

    axes_widget = widget._axes_widget
    assert axes_widget.axis_names() == ["0", "1"]
    assert list(map(QWidget.isEnabled, axes_widget.axis_widgets())) == [
        True,
        True,
    ]


def test_init_with_one_selected_2d_image(qtbot):
    viewer = ViewerModel()
    viewer.add_image(np.empty((4, 3)))
    assert viewer.layers.selection == {viewer.layers[0]}

    widget = make_metadata_widget(qtbot, viewer)

    axes_widget = widget._axes_widget
    assert axes_widget.axis_names() == ["0", "1"]
    assert list(map(QWidget.isEnabled, axes_widget.axis_widgets())) == [
        True,
        True,
    ]


def test_init_with_one_unselected_2d_image_and_one_selected_3d_image(
    qtbot,
):
    viewer = ViewerModel()
    viewer.add_image(np.empty((4, 3)))
    viewer.add_image(np.empty((4, 3, 2)))
    assert viewer.layers.selection == {viewer.layers[1]}

    widget = make_metadata_widget(qtbot, viewer)

    axes_widget = widget._axes_widget
    assert axes_widget.axis_names() == ["0", "1", "2"]
    assert list(map(QWidget.isEnabled, axes_widget.axis_widgets())) == [
        True,
        True,
        True,
    ]


def test_init_with_one_selected_2d_image_and_one_unselected_3d_image(
    qtbot,
):
    viewer = ViewerModel()
    viewer.add_image(np.empty((4, 3, 2)))
    viewer.add_image(np.empty((4, 3)))
    assert viewer.layers.selection == {viewer.layers[1]}

    widget = make_metadata_widget(qtbot, viewer)

    axes_widget = widget._axes_widget
    assert axes_widget.axis_names() == ["0", "1", "2"]
    assert list(map(QWidget.isEnabled, axes_widget.axis_widgets())) == [
        False,
        True,
        True,
    ]


def make_metadata_widget(qtbot, viewer) -> QMetadataWidget:
    widget = QMetadataWidget(viewer)
    qtbot.addWidget(widget)
    return widget
