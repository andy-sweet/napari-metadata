from copy import deepcopy
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    List,
    Optional,
    Protocol,
    Tuple,
    runtime_checkable,
)

from ._axis_type import AxisType
from ._space_units import SpaceUnits
from ._time_units import TimeUnits

if TYPE_CHECKING:
    from napari.components import ViewerModel
    from napari.layers import Layer


@runtime_checkable
class Axis(Protocol):
    name: str

    def get_type(self) -> AxisType:
        ...

    def get_unit_name(self) -> Optional[str]:
        ...


@dataclass
class SpaceAxis:
    name: str
    unit: SpaceUnits = SpaceUnits.NONE

    def get_type(self) -> AxisType:
        return AxisType.SPACE

    def get_unit_name(self) -> Optional[str]:
        return str(self.unit)


@dataclass
class TimeAxis:
    name: str
    unit: TimeUnits = TimeUnits.NONE

    def get_type(self) -> AxisType:
        return AxisType.TIME

    def get_unit_name(self) -> Optional[str]:
        return str(self.unit)


@dataclass
class ChannelAxis:
    name: str

    def get_type(self) -> AxisType:
        return AxisType.CHANNEL

    def get_unit_name(self) -> Optional[str]:
        return None


EXTRA_METADATA_KEY = "napari-metadata-plugin"


@dataclass
class OriginalMetadata:
    axes: Tuple[Axis]
    name: Optional[str]
    scale: Optional[Tuple[float, ...]]


@dataclass
class ExtraMetadata:
    axes: List[Axis]
    original: Optional[OriginalMetadata] = None


def get_layer_extra_metadata(layer: "Layer") -> Optional[ExtraMetadata]:
    return layer.metadata.get(EXTRA_METADATA_KEY)


def get_layer_axes(layer: "Layer") -> Tuple[Axis, ...]:
    extra_metadata = get_layer_extra_metadata(layer)
    if extra_metadata is None:
        return ()
    return tuple(extra_metadata.axes)


def get_layer_axis_types(layer: "Layer") -> Tuple[AxisType, ...]:
    extra_metadata = get_layer_extra_metadata(layer)
    if extra_metadata is None:
        return ()
    return tuple(axis.get_type() for axis in extra_metadata.axes)


def get_layer_axis_names(layer: "Layer") -> Tuple[str, ...]:
    extra_metadata = get_layer_extra_metadata(layer)
    if extra_metadata is None:
        return ()
    return tuple(axis.name for axis in extra_metadata.axes)


def get_layer_axis_unit_names(layer: "Layer") -> Tuple[str, ...]:
    extra_metadata = get_layer_extra_metadata(layer)
    if extra_metadata is None:
        return ()
    return tuple(axis.get_unit_name() for axis in extra_metadata.axes)


def get_layer_space_unit(layer: "Layer") -> SpaceUnits:
    space_axis_units = tuple(
        axis.unit
        for axis in get_layer_axes(layer)
        if isinstance(axis, SpaceAxis)
    )
    return (
        space_axis_units[0]
        if len(set(space_axis_units)) == 1
        else SpaceUnits.NONE
    )


# TODO: implementaton is almost the same as space, so refactor
# or overload/template the typing.
def get_layer_time_unit(layer: "Layer") -> TimeUnits:
    time_axis_units = tuple(
        axis.unit
        for axis in get_layer_axes(layer)
        if isinstance(axis, TimeAxis)
    )
    return (
        time_axis_units[0]
        if len(set(time_axis_units)) == 1
        else TimeUnits.NONE
    )


def set_layer_axes(layer: "Layer", axes: Tuple[Axis, ...]) -> None:
    layer.metadata[EXTRA_METADATA_KEY].axes = axes


def set_layer_axis_names(layer: "Layer", names: Tuple[str, ...]) -> None:
    extra_metadata = get_layer_extra_metadata(layer)
    if extra_metadata is None:
        return
    axes = extra_metadata.axes
    assert len(axes) == len(names)
    for axis, name in zip(axes, names):
        axis.name = name


def set_layer_space_unit(layer: "Layer", unit: SpaceUnits) -> None:
    extra_metadata = get_layer_extra_metadata(layer)
    if extra_metadata is None:
        return
    for axis in layer.metadata[EXTRA_METADATA_KEY].axes:
        if isinstance(axis, SpaceAxis):
            axis.unit = unit


def set_layer_time_unit(layer: "Layer", unit: TimeUnits) -> None:
    extra_metadata = get_layer_extra_metadata(layer)
    if extra_metadata is None:
        return
    for axis in layer.metadata[EXTRA_METADATA_KEY].axes:
        if isinstance(axis, TimeAxis):
            axis.unit = unit


def coerce_layer_extra_metadata(
    viewer: "ViewerModel", layer: Optional["Layer"]
) -> Optional["Layer"]:
    if layer is None:
        return None
    if EXTRA_METADATA_KEY in layer.metadata:
        if not isinstance(layer.metadata[EXTRA_METADATA_KEY], ExtraMetadata):
            return None
    else:
        axes = [
            SpaceAxis(name=name)
            for name in viewer.dims.axis_labels[-layer.ndim :]  # noqa
        ]
        original = OriginalMetadata(
            axes=tuple(deepcopy(axes)),
            name=layer.name,
            scale=tuple(layer.scale),
        )
        layer.metadata[EXTRA_METADATA_KEY] = ExtraMetadata(
            axes=axes,
            original=original,
        )
    return layer
