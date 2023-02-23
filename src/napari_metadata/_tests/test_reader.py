import numpy as np
import pytest
from napari.layers import Image

from .._model import (
    EXTRA_METADATA_KEY,
    ExtraMetadata,
    SpaceAxis,
    SpaceUnits,
    TimeAxis,
    TimeUnits,
)
from .._reader import read_ome_zarr
from .._writer import write_image


@pytest.fixture
def rng() -> np.random.Generator:
    return np.random.default_rng(0)


@pytest.fixture
def path(tmp_path) -> str:
    return str(tmp_path / "test.zarr")


def test_read_2d_image_without_extras(rng, path):
    image = Image(rng.random((5, 6)))
    data, metadata, _ = image.as_layer_data_tuple()
    paths_written = write_image(path, data, metadata)
    assert len(paths_written) == 1
    assert paths_written[0] == path

    read_layers = read_ome_zarr(path)

    assert len(read_layers) == 1
    read_data, _, _ = read_layers[0]
    np.testing.assert_array_equal(read_data, data)


def test_read_2d_image_with_extras(rng, path):
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
    assert len(paths_written) == 1
    assert paths_written[0] == path

    read_layers = read_ome_zarr(path)

    assert len(read_layers) == 1
    read_data, read_metadata, _ = read_layers[0]
    np.testing.assert_array_equal(read_data, data)

    assert read_metadata["name"] == "kermit"
    assert read_metadata["scale"] == (2, 3)
    assert read_metadata["translate"] == (-1, 1)

    read_extras: ExtraMetadata = read_metadata["metadata"][EXTRA_METADATA_KEY]
    assert len(read_extras.axes) == 2
    assert read_extras.axes[0] == extras.axes[0]
    assert read_extras.axes[1] == extras.axes[1]


def test_read_multiscale_2d_image_with_extras(rng, path):
    image = Image(
        [rng.random((10, 12)), rng.random((5, 6))],
        name="momo",
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
    assert len(paths_written) == 1
    assert paths_written[0] == path

    read_layers = read_ome_zarr(path)

    assert len(read_layers) == 1
    read_data, read_metadata, _ = read_layers[0]
    assert len(read_data) == 2
    np.testing.assert_array_equal(read_data[0], data[0])
    np.testing.assert_array_equal(read_data[1], data[1])

    assert read_metadata["name"] == "momo"
    assert read_metadata["scale"] == (2, 3)
    assert read_metadata["translate"] == (-1, 1)

    read_extras: ExtraMetadata = read_metadata["metadata"][EXTRA_METADATA_KEY]
    assert len(read_extras.axes) == 2
    assert read_extras.axes[0] == extras.axes[0]
    assert read_extras.axes[1] == extras.axes[1]


def test_read_3d_image_with_extras(rng, path):
    image = Image(
        rng.random((5, 6, 7)),
        name="sandy",
        scale=(1, 3, 4),
        translate=(9000, -1, 1),
    )
    data, metadata, _ = image.as_layer_data_tuple()
    extras = ExtraMetadata(
        axes=[
            TimeAxis(name="t", unit=TimeUnits.SECOND),
            SpaceAxis(name="y", unit=SpaceUnits.MILLIMETER),
            SpaceAxis(name="x", unit=SpaceUnits.MILLIMETER),
        ],
    )
    metadata["metadata"][EXTRA_METADATA_KEY] = extras
    paths_written = write_image(path, data, metadata)
    assert len(paths_written) == 1
    assert paths_written[0] == path

    read_layers = read_ome_zarr(path)

    assert len(read_layers) == 1
    read_data, read_metadata, _ = read_layers[0]
    np.testing.assert_array_equal(read_data, data)

    assert read_metadata["name"] == "sandy"
    assert read_metadata["scale"] == (1, 3, 4)
    assert read_metadata["translate"] == (9000, -1, 1)

    read_extras: ExtraMetadata = read_metadata["metadata"][EXTRA_METADATA_KEY]
    assert len(read_extras.axes) == 3
    assert read_extras.axes[0] == extras.axes[0]
    assert read_extras.axes[1] == extras.axes[1]
    assert read_extras.axes[2] == extras.axes[2]


def test_read_2d_image_with_mixed_space_units(rng, path):
    image = Image(np.zeros((5, 6)))
    data, metadata, _ = image.as_layer_data_tuple()
    extras = ExtraMetadata(
        axes=[
            SpaceAxis(name="y", unit=SpaceUnits.MILLIMETER),
            SpaceAxis(name="x", unit=SpaceUnits.METER),
        ],
    )
    metadata["metadata"][EXTRA_METADATA_KEY] = extras
    write_image(path, data, metadata)

    with pytest.warns(UserWarning):
        read_layers = read_ome_zarr(path)
    _, read_metadata, _ = read_layers[0]

    read_extras: ExtraMetadata = read_metadata["metadata"][EXTRA_METADATA_KEY]
    assert read_extras.axes[0] == SpaceAxis(name="y", unit=SpaceUnits.NONE)
    assert read_extras.axes[1] == SpaceAxis(name="x", unit=SpaceUnits.NONE)
