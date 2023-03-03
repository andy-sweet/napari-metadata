"""This module is a napari plugin.
It implements the ``napari_get_reader`` hook specification,
to create a reader plugin.

Vendored from v0.5.2 of napari-ome-zarr.
Modifications are indicated inline.

TODO: proper attribution for this.
"""

import logging
import warnings
from copy import deepcopy
from typing import Any, Dict, Iterator, List, Optional

import numpy as np
from ome_zarr.io import parse_url
from ome_zarr.reader import Label, Node, Reader
from ome_zarr.types import LayerData, PathLike, ReaderFunction
from vispy.color import Colormap

from ._model import (
    EXTRA_METADATA_KEY,
    Axis,
    ExtraMetadata,
    OriginalMetadata,
    SpaceAxis,
    TimeAxis,
)
from ._space_units import SpaceUnits
from ._time_units import TimeUnits

# MOD: change the name of the reader for this module.
LOGGER = logging.getLogger("napari_metadata._reader")

# NB: color for labels, colormap for images
# MOD: remove name from these, since it's a bit special.
METADATA_KEYS = ("visible", "contrast_limits", "colormap", "color", "metadata")


def napari_get_reader(path: PathLike) -> Optional[ReaderFunction]:
    """Returns a reader for supported paths that include IDR ID.
    - URL of the form: https://uk1s3.embassy.ebi.ac.uk/idr/zarr/v0.1/ID.zarr/
    """
    if isinstance(path, list):
        if len(path) > 1:
            warnings.warn("more than one path is not currently supported")
        path = path[0]
    zarr = parse_url(path)
    if zarr:
        reader = Reader(zarr)
        return transform(reader())
    # Ignoring this path
    return None


def transform_properties(
    props: Optional[Dict[str, Dict]] = None
) -> Optional[Dict[str, List]]:
    """
    Transform properties
    Transform a dict of {label_id : {key: value, key2: value2}}
    with a key for every LABEL
    into a dict of a key for every VALUE, with a list of values for each
    .. code::
        {
            "index": [1381342, 1381343...]
            "omero:roiId": [1381342, 1381343...],
            "omero:shapeId": [1682567, 1682567...]
        }
    """
    if props is None:
        return None

    properties: Dict[str, List] = {}

    # First, create lists for all existing keys...
    for label_id, props_dict in props.items():
        for key in props_dict.keys():
            properties[key] = []

    keys = list(properties.keys())

    properties["index"] = []
    for label_id, props_dict in props.items():
        properties["index"].append(label_id)
        # ...in case some objects don't have all the keys
        for key in keys:
            properties[key].append(props_dict.get(key, None))
    return properties


def transform_scale(
    node_metadata: Dict, metadata: Dict, channel_axis: Optional[int]
) -> None:
    """
    e.g. transformation is {"scale": [0.2, 0.06, 0.06]}
    Get a list of these for each level in data. Just use first?
    """
    if "coordinateTransformations" in node_metadata:
        level_0_transforms = node_metadata["coordinateTransformations"][0]
        for transf in level_0_transforms:
            if "scale" in transf:
                scale = transf["scale"]
                if channel_axis is not None:
                    scale.pop(channel_axis)
                metadata["scale"] = tuple(scale)
            if "translation" in transf:
                translate = transf["translation"]
                if channel_axis is not None:
                    translate.pop(channel_axis)
                metadata["translate"] = tuple(translate)


def transform(nodes: Iterator[Node]) -> Optional[ReaderFunction]:
    def f(*args: Any, **kwargs: Any) -> List[LayerData]:
        results: List[LayerData] = list()

        for node in nodes:
            data: List[Any] = node.data
            metadata: Dict[str, Any] = {}
            if data is None or len(data) < 1:
                LOGGER.debug(f"skipping non-data {node}")
            else:
                LOGGER.debug(f"transforming {node}")
                LOGGER.debug("node.metadata: %s" % node.metadata)

                layer_type: str = "image"
                channel_axis = None
                try:
                    ch_types = [axis["type"] for axis in node.metadata["axes"]]
                    if "channel" in ch_types:
                        channel_axis = ch_types.index("channel")
                except Exception:
                    LOGGER.error("Error reading axes: Please update ome-zarr")
                    raise

                transform_scale(node.metadata, metadata, channel_axis)

                # MOD: squeeze a single level image.
                if len(data) == 1:
                    data = data[0]

                # MOD: there is one name for all datasets and axes.
                if name := node.metadata.get("name"):
                    metadata["name"] = (
                        name if isinstance(name, str) else name[0]
                    )

                if node.load(Label):
                    layer_type = "labels"
                    for x in METADATA_KEYS:
                        if x in node.metadata:
                            metadata[x] = node.metadata[x]
                    if channel_axis is not None:
                        data = [
                            np.squeeze(level, axis=channel_axis)
                            for level in node.data
                        ]

                    # MOD: napari images don't support properties.
                    properties = transform_properties(
                        node.metadata.get("properties")
                    )
                    if properties is not None:
                        metadata["properties"] = properties

                else:
                    # Handle the removal of vispy requirement from ome-zarr-py
                    cms = node.metadata.get("colormap", [])
                    for idx, cm in enumerate(cms):
                        if not isinstance(cm, Colormap):
                            cms[idx] = Colormap(cm)

                    if channel_axis is not None:
                        # multi-channel; Copy known metadata values
                        metadata["channel_axis"] = channel_axis
                        for x in METADATA_KEYS:
                            if x in node.metadata:
                                metadata[x] = node.metadata[x]
                    else:
                        # single channel image, so metadata just needs
                        # single items (not lists)
                        for x in METADATA_KEYS:
                            if x in node.metadata:
                                try:
                                    metadata[x] = node.metadata[x][0]
                                except Exception:
                                    pass

                # MOD: this plugin provides somewhere to put the axes
                # and some extra metadata.
                axes = get_axes(node.metadata)
                original_meta = OriginalMetadata(
                    axes=deepcopy(axes),
                    name=metadata.get("name"),
                    scale=tuple(metadata["scale"])
                    if "scale" in metadata
                    else None,
                )
                extra_meta = ExtraMetadata(
                    axes=axes,
                    original=original_meta,
                )
                if "metadata" not in metadata:
                    metadata["metadata"] = dict()
                metadata["metadata"][EXTRA_METADATA_KEY] = extra_meta

                rv: LayerData = (data, metadata, layer_type)
                LOGGER.debug(f"Transformed: {rv}")
                results.append(rv)

        return results

    return f


def get_axes(metadata: Dict) -> List[Axis]:
    axes = []
    for a in metadata["axes"]:
        if axis := get_axis(a):
            axes.append(axis)
    space_axes = tuple(axis for axis in axes if isinstance(axis, SpaceAxis))
    space_units = {axis.get_unit_name() for axis in space_axes}
    if len(space_units) > 1:
        warnings.warn(
            f"Found mixed spatial units: {space_units}. "
            "Using none for all instead.",
            UserWarning,
        )
        for axis in space_axes:
            axis.unit = SpaceUnits.NONE
    return axes


def get_axis(axis: Dict) -> Optional[Axis]:
    name = axis["name"]
    unit = axis.get("unit", "none")
    axis_type = axis.get("type")
    if axis_type == "time":
        return TimeAxis(name=name, unit=TimeUnits.from_name(unit))
    elif axis_type != "channel":
        return SpaceAxis(name=name, unit=SpaceUnits.from_name(unit))
    return None
