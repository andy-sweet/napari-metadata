from typing import Dict, Tuple

import numpy as np
import pytest
from npe2.types import ArrayLike
from ome_zarr.io import parse_url
from ome_zarr.reader import Reader

from .._model import EXTRA_METADATA_KEY, ExtraMetadata, SpaceAxis, SpaceUnits
from .._writer import write_image


@pytest.fixture
def rng() -> np.random.Generator:
    return np.random.default_rng(0)


@pytest.fixture
def path(tmp_path) -> str:
    return str(tmp_path / "test.zarr")


def read_ome_zarr(path: str) -> Tuple[ArrayLike, Dict]:
    reader = Reader(parse_url(path))
    nodes = list(reader())
    data = nodes[0].data[0]
    metadata = nodes[0].metadata
    return data, metadata


def test_write_2d_image_without_extras(rng, path):
    data = rng.random((5, 6))

    paths_written = write_image(path, data, {})

    assert len(paths_written) == 1
    assert paths_written[0] == path

    read_data, read_metadata = read_ome_zarr(path)

    np.testing.assert_array_equal(read_data, data)

    axes = read_metadata["axes"]
    axis_names = tuple(a["name"] for a in axes)
    assert axis_names == ("0", "1")

    axis_types = tuple(a["type"] for a in axes)
    assert axis_types == ("space", "space")

    axis_units = tuple(a.get("unit") for a in axes)
    assert axis_units == (None, None)


def test_write_2d_image_with_extras(rng, path):
    data = rng.random((5, 6))
    metadata = {
        EXTRA_METADATA_KEY: ExtraMetadata(
            axes=[
                SpaceAxis(name="y", unit=SpaceUnits.MILLIMETER),
                SpaceAxis(name="x", unit=SpaceUnits.MILLIMETER),
            ]
        )
    }

    paths_written = write_image(path, data, metadata)

    assert len(paths_written) == 1
    assert paths_written[0] == path

    read_data, read_metadata = read_ome_zarr(path)

    np.testing.assert_array_equal(read_data, data)

    axes = read_metadata["axes"]
    axis_names = tuple(a["name"] for a in axes)
    assert axis_names == ("y", "x")

    axis_types = tuple(a["type"] for a in axes)
    assert axis_types == ("space", "space")

    axis_units = tuple(a.get("unit") for a in axes)
    assert axis_units == ("millimeter", "millimeter")
