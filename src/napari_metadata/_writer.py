import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Sequence

import numpy as np
import zarr
from npe2.types import ArrayLike
from ome_zarr.io import parse_url
from ome_zarr.writer import write_multiscale, write_multiscales_metadata

from ._model import EXTRA_METADATA_KEY, Axis

if TYPE_CHECKING:
    from napari.layers import Layer


@dataclass
class OmeMetadata:
    name: str
    axes: List[Dict[str, str]]
    transforms: List[List[Dict[str, Any]]]


def write_image(
    path: str, data: ArrayLike, attributes: Dict[str, Any]
) -> List[str]:
    # Based on https://ome-zarr.readthedocs.io/en/stable/python.html#writing-ome-ngff-images # noqa
    os.mkdir(path)

    store = parse_url(path, mode="w").store
    root = zarr.group(store=store)

    data = data if isinstance(data, Sequence) else [data]
    metadata = multiscales_metadata(data, attributes)

    write_multiscale(
        pyramid=data,
        group=root,
        name=metadata.name,
        axes=metadata.axes,
        coordinate_transformations=metadata.transforms,
    )

    return [path]


def writable_image_group(layer: "Layer") -> Optional[zarr.Group]:
    source = layer.source
    reader = source.reader_plugin
    # We need write access to the zarr group that was read with this plugin.
    if reader != "napari-metadata":
        return
    path = source.path
    if path is None:
        return
    location = parse_url(path, mode="w")
    if location is None:
        return
    return zarr.group(store=location.store)


def overwrite_metadata(layer: "Layer") -> None:
    group = writable_image_group(layer)
    if group is None:
        return

    multiscales = group.attrs.get("multiscales")
    if multiscales is None:
        return

    # We only expect one multiscale image in the group.
    if len(multiscales) != 1:
        return

    # Now everything looks good, lets extract the layer's updated metadata.
    data, attributes, _ = layer.as_layer_data_tuple()
    metadata = multiscales_metadata(data, attributes)

    # Update the datasets in place with the updated transforms.
    # NB: this is potentially lossy since napari does not have a transform
    # sequence associated with a layer, so we may want to back out here
    # in some cases.
    datasets = multiscales[0]["datasets"]
    assert len(metadata.transforms) == len(datasets)
    for i in range(len(datasets)):
        datasets[i]["coordinateTransformations"] = metadata.transforms[i]

    write_multiscales_metadata(
        group=group,
        datasets=datasets,
        name=metadata.name,
        axes=metadata.axes,
    )


def multiscales_metadata(
    data: ArrayLike, attributes: Dict[str, Any]
) -> OmeMetadata:
    data = data if isinstance(data, Sequence) else [data]

    if extras := attributes["metadata"].get(EXTRA_METADATA_KEY):
        axes = [axis_to_ome(axis) for axis in extras.axes]
    else:
        # Ideally we would just provide axis names, but that it not
        # currently possible:
        # https://github.com/ome/ome-zarr-py/issues/249
        # so use space as the most sensible default.
        axes = [
            {"name": str(i), "type": "space"}
            for i in range(len(data[0].shape))
        ]

    name = attributes["name"]

    scale_factors = [np.divide(data[0].shape, d.shape) for d in data]

    transforms = [
        [
            {
                "type": "scale",
                "scale": tuple(scale_factor * attributes["scale"]),
            },
            {
                "type": "translation",
                "translation": attributes["translate"],
            },
        ]
        for scale_factor in scale_factors
    ]

    return OmeMetadata(
        name=name,
        axes=axes,
        transforms=transforms,
    )


def axis_to_ome(axis: Axis) -> Dict[str, str]:
    ome = {
        "name": axis.name,
        "type": str(axis.get_type()),
    }
    if unit := axis.get_unit_name():
        ome["unit"] = unit
    return ome
