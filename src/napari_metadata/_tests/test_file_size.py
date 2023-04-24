from napari_metadata._file_size import generate_text_for_size, generate_display_size, zarr_directory_size
from napari.layers import Image
import pytest
from napari_metadata._model import (
    EXTRA_METADATA_KEY,
    ExtraMetadata,
    SpaceAxis,
    SpaceUnits,
)
from napari_metadata._reader import napari_get_reader
from napari_metadata._writer import write_image
from pathlib import Path



@pytest.fixture
def local_zarr_path(rng, path):
    image = Image(
        rng.random((5, 6)),
        name="kermit",
        scale=(2, 3),
        translate=(-1, 1),
    )
    data, metadata, _ = image.as_layer_data_tuple()
    extras = ExtraMetadata(
        axes=[
            SpaceAxis(name="y", unit=SpaceUnits.MILLIMETER),
            SpaceAxis(name="x", unit=SpaceUnits.MILLIMETER),
        ],
    )
    metadata["metadata"][EXTRA_METADATA_KEY] = extras
    paths_written = write_image(path, data, metadata)
    return paths_written[0]


def test_local_file_new(local_zarr_path):
    reader = napari_get_reader(local_zarr_path)
    layerdata_tuples = reader(local_zarr_path) # [(data, metadata, layer_type)]
    data, metadata, layer_type = layerdata_tuples[0]

    layer = Image(data, metadata=metadata)
    text = generate_display_size(layer)
    # the Source will not be set properly so even local zarr files will not 
    # have a path set
    assert not layer.source.path
    assert 'in memory' in text


def test_zarr_directory_size(local_zarr_path):
    read_bytes = zarr_directory_size(local_zarr_path)
    expected_bytes = 1893

    assert pytest.approx(read_bytes, 100) == expected_bytes


def test_generate_text_for_size():
    size = 13
    text = generate_text_for_size(size)
    assert text == '13.00 bytes'

    size = 130
    text = generate_text_for_size(size)
    assert text == '130.00 bytes'

    size = 1303
    text = generate_text_for_size(size)
    assert text == '1.30 KB'

    size = 13031
    text = generate_text_for_size(size)
    assert text == '13.03 KB'

    size = 130313
    text = generate_text_for_size(size)
    assert text == '130.31 KB'

    size = 1303131
    text = generate_text_for_size(size)
    assert text == '1.30 MB'

    size = 13031319
    text = generate_text_for_size(size)
    assert text == '13.03 MB'

    size = 130313190
    text = generate_text_for_size(size)
    assert text == '130.31 MB'

    size = 1303131900
    text = generate_text_for_size(size)
    assert text == '1.30 GB'


def test_generate_text_for_size_with_suffix():
    size = 13
    suffix = ' (in memory)'
    text = generate_text_for_size(size, suffix=suffix)
    assert text == f'13.00 bytes{suffix}'


def test_no_path(rng):
    layer = Image(rng.random((5, 6)))
    text = generate_display_size(layer)
    # ensure layer does not have a path set
    assert not layer.source.path
    # if no source path, get in memory size
    assert 'in memory' in text
