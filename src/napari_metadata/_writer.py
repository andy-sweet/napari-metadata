import os
from typing import Any, Dict, List, Sequence

import zarr
from npe2.types import ArrayLike
from ome_zarr.io import parse_url
from ome_zarr.writer import write_multiscale

from ._model import EXTRA_METADATA_KEY, Axis


def write_image(
    path: str, data: ArrayLike, attributes: Dict[str, Any]
) -> List[str]:
    # Based on https://ome-zarr.readthedocs.io/en/stable/python.html#writing-ome-ngff-images # noqa
    os.mkdir(path)

    store = parse_url(path, mode="w").store
    root = zarr.group(store=store)

    if extras := attributes.get(EXTRA_METADATA_KEY):
        axes = [axis_to_ome(axis) for axis in extras.axes]
    else:
        axes = [
            {"name": str(i), "type": "space"} for i in range(len(data.shape))
        ]

    multiscale_data = data if isinstance(data, Sequence) else [data]

    write_multiscale(
        pyramid=multiscale_data,
        group=root,
        axes=axes,
    )

    return [path]


def axis_to_ome(axis: Axis) -> Dict[str, str]:
    ome = {
        "name": axis.name,
        "type": str(axis.get_type()),
    }
    if unit := axis.get_unit_name():
        ome["unit"] = unit
    return ome
