from typing import Dict, Optional, Tuple

import numpy as np
import pytest
from napari.layers import Image
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


def ome_axis_names(ome_metadata: Dict) -> Tuple[str, ...]:
    return tuple(a["name"] for a in ome_metadata["axes"])


def ome_axis_types(ome_metadata: Dict) -> Tuple[Optional[str], ...]:
    return tuple(a.get("type") for a in ome_metadata["axes"])


def ome_axis_units(ome_metadata: Dict) -> Tuple[Optional[str], ...]:
    return tuple(a.get("unit") for a in ome_metadata["axes"])


def ome_transforms(ome_metadata: Dict) -> Tuple[float, ...]:
    return ome_metadata["coordinateTransformations"][0]


def test_write_2d_image_without_extras(rng, path):
    image = Image(rng.random((5, 6)))
    data, metadata, _ = image.as_layer_data_tuple()

    paths_written = write_image(path, data, metadata)

    assert len(paths_written) == 1
    assert paths_written[0] == path

    read_data, read_metadata = read_ome_zarr(path)

    np.testing.assert_array_equal(read_data, data)

    # The default/magic name that napari gives the layer is not
    # in our control and we always write it.
    assert read_metadata["name"] == "Image"

    assert ome_axis_names(read_metadata) == ("0", "1")
    assert ome_axis_types(read_metadata) == ("space", "space")
    assert ome_axis_units(read_metadata) == (None, None)

    transforms = read_metadata["coordinateTransformations"][0]
    assert len(transforms) == 2
    assert tuple(transforms[0]["scale"]) == (1, 1)
    assert tuple(transforms[1]["translation"]) == (0, 0)


def test_write_2d_image_with_extras(rng, path):
    image = Image(
        rng.random((5, 6)), name="kermit", scale=(2, 3), translate=(-1, 1)
    )
    data, metadata, _ = image.as_layer_data_tuple()
    metadata[EXTRA_METADATA_KEY] = ExtraMetadata(
        axes=[
            SpaceAxis(name="y", unit=SpaceUnits.MILLIMETER),
            SpaceAxis(name="x", unit=SpaceUnits.MILLIMETER),
        ],
    )

    paths_written = write_image(path, data, metadata)

    assert len(paths_written) == 1
    assert paths_written[0] == path

    read_data, read_metadata = read_ome_zarr(path)

    np.testing.assert_array_equal(read_data, data)

    assert read_metadata["name"] == "kermit"

    assert ome_axis_names(read_metadata) == ("y", "x")
    assert ome_axis_types(read_metadata) == ("space", "space")
    assert ome_axis_units(read_metadata) == ("millimeter", "millimeter")

    transforms = read_metadata["coordinateTransformations"][0]
    assert len(transforms) == 2
    assert tuple(transforms[0]["scale"]) == (2, 3)
    assert tuple(transforms[1]["translation"]) == (-1, 1)
