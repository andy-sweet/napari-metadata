from typing import TYPE_CHECKING, Dict, List, Optional

from pint import Unit, UnitRegistry
from qtpy.QtWidgets import QComboBox, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from napari_metadata._axis_type import AxisType
from napari_metadata._space_units import SpaceUnits
from napari_metadata._time_units import TimeUnits

if TYPE_CHECKING:
    from napari.components import ViewerModel


class AxisTypeUnitsWidget(QWidget):
    """Shows and controls one axis type's units."""

    def __init__(
        self, parent: Optional["QWidget"], name: str, unit_types: List[str]
    ) -> None:
        super().__init__(parent)
        self.type = QLabel(name)
        self.units = QComboBox()
        self.units.addItems(unit_types)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.type)
        layout.addWidget(self.units)
        self.setLayout(layout)


class AxesTypeUnitsWidget(QWidget):
    """Shows and controls all axis types' units."""

    def __init__(self, viewer: "ViewerModel") -> None:
        super().__init__()
        self._viewer: "ViewerModel" = viewer
        self._unit_registry: UnitRegistry = UnitRegistry()
        self._PINT_TO_SPACE_UNIT: Dict[Unit, SpaceUnits] = {
            self._unit_registry.nanometer: SpaceUnits.NANOMETERS,
            self._unit_registry.micron: SpaceUnits.MICROMETERS,
            self._unit_registry.micrometer: SpaceUnits.MICROMETERS,
            self._unit_registry.millimeter: SpaceUnits.MILLIMETERS,
            self._unit_registry.centimeter: SpaceUnits.CENTIMETERS,
            self._unit_registry.meter: SpaceUnits.METERS,
        }

        self.space = AxisTypeUnitsWidget(
            self, str(AxisType.SPACE), SpaceUnits.names()
        )
        self.time = AxisTypeUnitsWidget(
            self, str(AxisType.TIME), TimeUnits.names()
        )

        layout = QVBoxLayout()
        layout.addWidget(self.space)
        layout.addWidget(self.time)
        self.setLayout(layout)

        self._viewer.scale_bar.events.unit.connect(
            self._on_viewer_scale_bar_unit_changed
        )
        self.space.units.currentTextChanged.connect(
            self._on_space_units_changed
        )

        self._on_space_units_changed()

    def _on_space_units_changed(self) -> None:
        text = self.space.units.currentText()
        unit = None if text == "none" else text
        self._viewer.scale_bar.unit = unit

    def _on_viewer_scale_bar_unit_changed(self, event) -> None:
        unit = event.value
        text = "none" if unit is None else self._convert_model_unit(unit)
        self.space.units.setCurrentText(text)

    def _convert_model_unit(self, model_unit: str) -> str:
        quantity = self._unit_registry(model_unit)
        if quantity is None:
            return "none"
        unit = quantity.units
        if unit not in self._PINT_TO_SPACE_UNIT:
            return "none"
        return str(self._PINT_TO_SPACE_UNIT[unit])
