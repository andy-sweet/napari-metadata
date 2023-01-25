from napari_metadata import QMetadataWidget


def test_init(make_napari_viewer):
    viewer = make_napari_viewer()
    QMetadataWidget(viewer)
