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


def get_readonly_reason(layer: "Layer") -> Optional[str]:
    try:
        _ = writable_image_group(layer)
    except ValueError as e:
        return str(e)
    return None


def writable_image_group(layer: "Layer") -> zarr.Group:
    source = layer.source
    reader = source.reader_plugin
    if reader != "napari-metadata":
        raise ValueError(
            "the layer was not opened with the napari-metadata plugin"
        )
    path = source.path
    if path is None:
        raise ValueError("the layer was not read from a path")
    location = parse_url(path, mode="w")
    if location is None:
        raise ValueError(
            "the layer's path was not recognized as a writable zarr"
        )

    group = zarr.group(store=location.store)

    multiscales = group.attrs.get("multiscales")
    if (multiscales is None) or (len(multiscales) != 1):
        raise ValueError("the layer is not an ome-zarr multiscale image")
    multiscale = multiscales[0]

    data, attributes, _ = layer.as_layer_data_tuple()
    metadata = multiscales_metadata(data, attributes)

    datasets = multiscale["datasets"]
    num_levels_layer = len(metadata.transforms)
    num_levels_zarr = len(datasets)
    if num_levels_layer != num_levels_zarr:
        raise ValueError(
            "the number of multiscale levels in the layer "
            f"({num_levels_layer}) is different to that of the ome-zarr "
            f"({num_levels_zarr})"
        )

    num_axes_layer = len(metadata.axes)
    num_axes_zarr = len(multiscale["axes"])
    if num_axes_layer != num_axes_zarr:
        raise ValueError(
            f"the number of axes in the layer ({num_axes_layer})"
            "is different to that of the ome-zarr ({num_axes_zarr})"
        )

    return group


def overwrite_metadata(layer: "Layer") -> None:
    group = writable_image_group(layer)

    # Now everything looks good, lets extract the layer's updated metadata.
    data, attributes, _ = layer.as_layer_data_tuple()
    metadata = multiscales_metadata(data, attributes)

    # Update the datasets in place with the updated transforms.
    # NB: this is potentially lossy since napari does not have a transform
    # sequence associated with a layer, so we may want to back out here
    # in some cases.
    multiscales = group.attrs.get("multiscales")
    datasets = multiscales[0]["datasets"]
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
