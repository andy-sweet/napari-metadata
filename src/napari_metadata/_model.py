from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Protocol, Tuple, runtime_checkable

from ._axis_type import AxisType
from ._space_units import SpaceUnits
from ._time_units import TimeUnits

if TYPE_CHECKING:
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
class ExtraMetadata:
    axes: Tuple[Axis, ...]
    experiment_id: str = ""

    @classmethod
    def from_layer(cls, layer: "Layer") -> "ExtraMetadata":
        return ExtraMetadata(
            axes=tuple(SpaceAxis(name=str(i)) for i in range(layer.ndim)),
        )


def get_layer_extra_metadata(layer: "Layer") -> Optional[ExtraMetadata]:
    return layer.metadata.get(EXTRA_METADATA_KEY)


def get_layer_axis_names(layer: "Layer") -> Tuple[str, ...]:
    extra_metadata = get_layer_extra_metadata(layer)
    return tuple(axis.name for axis in extra_metadata.axes)


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
    for axis in layer.metadata[EXTRA_METADATA_KEY].axes:
        if isinstance(axis, SpaceAxis):
            axis.unit = unit


def set_layer_time_unit(layer: "Layer", unit: TimeUnits) -> None:
    for axis in layer.metadata[EXTRA_METADATA_KEY].axes:
        if isinstance(axis, TimeAxis):
            axis.unit = unit


def coerce_layer_extra_metadata(layer: Optional["Layer"]) -> Optional["Layer"]:
    if layer is None:
        return None
    if EXTRA_METADATA_KEY in layer.metadata:
        if not isinstance(layer.metadata[EXTRA_METADATA_KEY], ExtraMetadata):
            return None
    else:
        layer.metadata[EXTRA_METADATA_KEY] = ExtraMetadata.from_layer(layer)
    return layer
