from typing import Tuple

import numpy as np
from napari.components import ViewerModel
from qtpy.QtWidgets import QWidget

from napari_metadata import QMetadataWidget


def test_init_with_no_layers(qtbot):
    viewer = ViewerModel()
    assert viewer.layers.selection == set()

    widget = make_metadata_widget(qtbot, viewer)

    assert axis_names(widget) == ("0", "1")
    assert are_axis_widgets_enabled(widget) == (True, True)


def test_init_with_one_selected_2d_image(qtbot):
    viewer = ViewerModel()
    viewer.add_image(np.empty((4, 3)))
    assert viewer.layers.selection == {viewer.layers[0]}

    widget = make_metadata_widget(qtbot, viewer)

    assert axis_names(widget) == ("0", "1")
    assert are_axis_widgets_enabled(widget) == (True, True)


def test_init_with_one_unselected_2d_image_and_one_selected_3d_image(
    qtbot,
):
    viewer = ViewerModel()
    viewer.add_image(np.empty((4, 3)))
    viewer.add_image(np.empty((4, 3, 2)))
    assert viewer.layers.selection == {viewer.layers[1]}

    widget = make_metadata_widget(qtbot, viewer)

    assert axis_names(widget) == ("0", "1", "2")
    assert are_axis_widgets_enabled(widget) == (True, True, True)


def test_init_with_one_selected_2d_image_and_one_unselected_3d_image(
    qtbot,
):
    viewer = ViewerModel()
    viewer.add_image(np.empty((4, 3, 2)))
    viewer.add_image(np.empty((4, 3)))
    assert viewer.layers.selection == {viewer.layers[1]}

    widget = make_metadata_widget(qtbot, viewer)

    assert axis_names(widget) == ("0", "1", "2")
    assert are_axis_widgets_enabled(widget) == (False, True, True)


def axis_names(widget: QMetadataWidget) -> Tuple[str]:
    return tuple(widget._axes_widget.axis_names())


def are_axis_widgets_enabled(widget: QMetadataWidget) -> Tuple[bool]:
    axes_widget = widget._axes_widget
    return tuple(map(QWidget.isEnabled, axes_widget.axis_widgets()))


def make_metadata_widget(qtbot, viewer) -> QMetadataWidget:
    widget = QMetadataWidget(viewer)
    qtbot.addWidget(widget)
    return widget
