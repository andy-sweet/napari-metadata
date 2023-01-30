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


def test_selected_layer_from_2d_to_3d(qtbot):
    viewer = ViewerModel()
    viewer.add_image(np.empty((4, 3, 2)))
    viewer.add_image(np.empty((4, 3)))
    assert viewer.layers.selection == {viewer.layers[1]}
    widget = make_metadata_widget(qtbot, viewer)
    assert are_axis_widgets_enabled(widget) == (False, True, True)

    viewer.layers.selection = {viewer.layers[0]}

    assert are_axis_widgets_enabled(widget) == (True, True, True)


def test_selected_layer_from_3d_to_2d(qtbot):
    viewer = ViewerModel()
    viewer.add_image(np.empty((4, 3)))
    viewer.add_image(np.empty((4, 3, 2)))
    assert viewer.layers.selection == {viewer.layers[1]}
    widget = make_metadata_widget(qtbot, viewer)
    assert are_axis_widgets_enabled(widget) == (True, True, True)

    viewer.layers.selection = {viewer.layers[0]}

    assert are_axis_widgets_enabled(widget) == (False, True, True)


def test_add_2d_image_to_3d_image(qtbot):
    viewer = ViewerModel()
    viewer.add_image(np.empty((4, 3, 2)))
    assert viewer.layers.selection == {viewer.layers[0]}
    widget = make_metadata_widget(qtbot, viewer)
    assert are_axis_widgets_enabled(widget) == (True, True, True)

    viewer.add_image(np.empty((4, 3)))

    assert viewer.layers.selection == {viewer.layers[1]}
    assert are_axis_widgets_enabled(widget) == (False, True, True)


def test_add_3d_image_to_2d_image(qtbot):
    viewer = ViewerModel()
    viewer.add_image(np.empty((4, 3)))
    assert viewer.layers.selection == {viewer.layers[0]}
    widget = make_metadata_widget(qtbot, viewer)
    assert are_axis_widgets_enabled(widget) == (True, True)

    viewer.add_image(np.empty((4, 3, 2)))

    assert viewer.layers.selection == {viewer.layers[1]}
    assert are_axis_widgets_enabled(widget) == (True, True, True)


def test_changing_axis_name_changes_viewer_axis_label(qtbot):
    viewer = ViewerModel()
    viewer.add_image(np.empty((4, 3)))
    assert viewer.layers.selection == {viewer.layers[0]}
    widget = make_metadata_widget(qtbot, viewer)
    first_axis_widget = widget._axes_widget.axis_widgets()[0]
    new_name = "y"
    assert first_axis_widget.name.text() != new_name
    assert viewer.dims.axis_labels[0] != new_name

    first_axis_widget.name.setText(new_name)

    assert viewer.dims.axis_labels[0] == new_name


def test_changing_viewer_axis_label_changes_axis_name(qtbot):
    viewer = ViewerModel()
    viewer.add_image(np.empty((4, 3)))
    assert viewer.layers.selection == {viewer.layers[0]}
    widget = make_metadata_widget(qtbot, viewer)
    first_axis_widget = widget._axes_widget.axis_widgets()[0]
    new_name = "y"
    assert viewer.dims.axis_labels[0] != new_name
    assert first_axis_widget.name.text() != new_name

    viewer.dims.axis_labels = [new_name, viewer.dims.axis_labels[1]]

    assert first_axis_widget.name.text() == new_name


def test_changing_space_unit_changes_viewer_scale_bar_unit(qtbot):
    viewer = ViewerModel()
    viewer.add_image(np.empty((4, 3)))
    assert viewer.layers.selection == {viewer.layers[0]}
    widget = make_metadata_widget(qtbot, viewer)
    space_units_widget = widget._types_widget.space.units
    new_unit = "millimeters"
    assert space_units_widget.currentText() != new_unit
    assert viewer.scale_bar.unit != new_unit

    space_units_widget.setCurrentText(new_unit)

    assert viewer.scale_bar.unit == new_unit


def test_changing_viewer_scale_bar_unit_changes_space_unit(qtbot):
    viewer = ViewerModel()
    viewer.add_image(np.empty((4, 3)))
    assert viewer.layers.selection == {viewer.layers[0]}
    widget = make_metadata_widget(qtbot, viewer)
    space_units_widget = widget._types_widget.space.units
    new_unit = "millimeters"
    assert viewer.scale_bar.unit != new_unit
    assert space_units_widget.currentText() != new_unit

    viewer.scale_bar.unit = new_unit

    assert space_units_widget.currentText() == new_unit


def test_changing_viewer_scale_bar_unit_to_none_changes_space_unit(qtbot):
    viewer = ViewerModel()
    viewer.add_image(np.empty((4, 3)))
    assert viewer.layers.selection == {viewer.layers[0]}
    widget = make_metadata_widget(qtbot, viewer)
    space_units_widget = widget._types_widget.space.units
    viewer.scale_bar.unit = "millimeters"
    assert space_units_widget.currentText() != "none"

    viewer.scale_bar.unit = None

    assert space_units_widget.currentText() == "none"


def test_changing_viewer_scale_bar_unit_to_unknown_changes_space_unit(qtbot):
    viewer = ViewerModel()
    viewer.add_image(np.empty((4, 3)))
    assert viewer.layers.selection == {viewer.layers[0]}
    widget = make_metadata_widget(qtbot, viewer)
    viewer.scale_bar.unit = "millimeters"
    space_units_widget = widget._types_widget.space.units
    assert space_units_widget.currentText() != "none"

    # Supported by pint/napari, but not supported by our widget.
    viewer.scale_bar.unit = "furlongs"

    assert space_units_widget.currentText() == "none"
    # TODO: decide if this should pass.
    # assert viewer.scale_bar.unit == "furlongs"


def test_changing_viewer_scale_bar_unit_to_abbreviation(qtbot):
    viewer = ViewerModel()
    viewer.add_image(np.empty((4, 3)))
    assert viewer.layers.selection == {viewer.layers[0]}
    widget = make_metadata_widget(qtbot, viewer)
    space_units_widget = widget._types_widget.space.units
    assert viewer.scale_bar.unit != "mm"
    assert space_units_widget.currentText() != "millimeters"

    viewer.scale_bar.unit = "mm"

    assert space_units_widget.currentText() == "millimeters"


def axis_names(widget: QMetadataWidget) -> Tuple[str]:
    return tuple(widget._axes_widget.axis_names())


def are_axis_widgets_enabled(widget: QMetadataWidget) -> Tuple[bool]:
    axes_widget = widget._axes_widget
    return tuple(map(QWidget.isEnabled, axes_widget.axis_widgets()))


def make_metadata_widget(qtbot, viewer) -> QMetadataWidget:
    widget = QMetadataWidget(viewer)
    qtbot.addWidget(widget)
    return widget
