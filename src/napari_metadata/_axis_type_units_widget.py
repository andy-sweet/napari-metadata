from typing import TYPE_CHECKING, List, Optional

from qtpy.QtWidgets import QComboBox, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from napari_metadata._axis_type import AxisType
from napari_metadata._space_units import SpaceUnits
from napari_metadata._time_units import TimeUnits

if TYPE_CHECKING:
    from napari.components import ViewerModel


class AxisTypeUnitsWidget(QWidget):
    def __init__(
        self, parent: Optional["QWidget"], name: str, unit_types: List[str]
    ) -> None:
        super().__init__(parent)
        self.setLayout(QHBoxLayout())
        self.type = QLabel(name)
        self.layout().addWidget(self.type)
        self.units = QComboBox()
        self.units.addItems(unit_types)
        self.layout().addWidget(self.units)


class AxesTypeUnitsWidget(QWidget):
    def __init__(self, viewer: "ViewerModel") -> None:
        super().__init__()
        self._viewer: "ViewerModel" = viewer

        self.space = AxisTypeUnitsWidget(
            self, str(AxisType.SPACE), SpaceUnits.names()
        )
        self.time = AxisTypeUnitsWidget(
            self, str(AxisType.TIME), TimeUnits.names()
        )

        layout = QVBoxLayout()
        layout.addWidget(QLabel("View and edit viewer axis units"))
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
        self._viewer.scale_bar.unit = self.space.units.currentText()

    def _on_viewer_scale_bar_unit_changed(self, event) -> None:
        self.space.units.setCurrentText(event.value)
