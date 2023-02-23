# Some of this is copied from napari-ome-zarr.
# TODO: proper attribution for this or write my own.

import logging
import warnings
from typing import Any, Dict, List, Optional

from ome_zarr.io import parse_url
from ome_zarr.reader import Reader
from ome_zarr.types import LayerData, PathLike, ReaderFunction

from ._model import EXTRA_METADATA_KEY, ExtraMetadata, SpaceAxis, TimeAxis
from ._space_units import SpaceUnits
from ._time_units import TimeUnits

LOGGER = logging.getLogger("napari_metadata._reader")


def napari_get_reader(path: PathLike) -> Optional[ReaderFunction]:
    if isinstance(path, list):
        if len(path) > 1:
            warnings.warn("more than one path is not currently supported")
        path = path[0]
    return read_ome_zarr


def read_ome_zarr(path: PathLike) -> List[LayerData]:
    zarr = parse_url(path)
    if zarr is None:
        return None

    results: List[LayerData] = []
    reader = Reader(zarr)
    nodes = reader()
    for node in nodes:
        data: List[Any] = node.data

        if data is None or len(data) < 1:
            LOGGER.debug("skipping non-data %s", node)
            continue

        # Squeeze single-level images.
        if len(data) == 1:
            data = data[0]

        metadata: Dict[str, Any] = {}

        if "coordinateTransformations" in node.metadata:
            level_0_transforms = node.metadata["coordinateTransformations"][0]
            for transform in level_0_transforms:
                if "scale" in transform:
                    metadata["scale"] = tuple(transform["scale"])
                if "translation" in transform:
                    metadata["translate"] = tuple(transform["translation"])

        if "name" in node.metadata:
            metadata["name"] = node.metadata["name"]

        # Extra reads for this plugin.
        axes = []
        for a in node.metadata["axes"]:
            name = a["name"]
            unit = a.get("unit", "none")
            # TODO: support channel axes.
            if a["type"] == "time":
                axis = TimeAxis(name=name, unit=TimeUnits.from_name(unit))
            else:
                axis = SpaceAxis(name=name, unit=SpaceUnits.from_name(unit))
            axes.append(axis)

        space_axes = tuple(
            axis for axis in axes if isinstance(axis, SpaceAxis)
        )
        space_units = {axis.get_unit_name() for axis in space_axes}
        if len(space_units) > 1:
            warnings.warn(
                f"Found mixed spatial units: {space_units}"
                "Using none for all.",
                UserWarning,
            )
            for axis in space_axes:
                axis.unit = SpaceUnits.NONE

        metadata["metadata"] = {
            EXTRA_METADATA_KEY: ExtraMetadata(axes=axes),
        }

        results.append((data, metadata, "image"))

        return results
