import numpy as np
import pytest
from napari.layers import Image

from .._model import EXTRA_METADATA_KEY, ExtraMetadata, SpaceAxis, SpaceUnits
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


def test_write_2d_image_with_extras(rng, path):
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
