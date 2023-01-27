from napari.components import ViewerModel

from napari_metadata import QMetadataWidget


def test_init(qtbot):
    viewer = ViewerModel()
    widget = QMetadataWidget(viewer)
    qtbot.addWidget(widget)
