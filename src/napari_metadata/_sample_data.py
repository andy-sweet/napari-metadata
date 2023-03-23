from copy import deepcopy
from typing import TYPE_CHECKING, Dict, List, Tuple

import numpy as np
from skimage.data import cells3d

from napari_metadata._model import (
    EXTRA_METADATA_KEY,
    ExtraMetadata,
    OriginalMetadata,
    SpaceAxis,
    SpaceUnits,
)

if TYPE_CHECKING:
    from npe2.types import LayerData


def make_nuclei_md_sample_data() -> List["LayerData"]:
    all_data = cells3d()

    nuclei_data = all_data[:, 1, :, :]
    nuclei_metadata = _make_metadata(
        name="nuclei",
        scale=(2, 1, 1),
        colormap="green",
        axis_names=("z", "y", "x"),
    )

    mean_nuclei_data = np.mean(nuclei_data, axis=0)
    mean_nuclei_metadata = _make_metadata(
        name="nuclei_mean",
        scale=(1, 1),
        colormap="blue",
        axis_names=("y", "x"),
    )

    return [
        (nuclei_data, nuclei_metadata),
        (mean_nuclei_data, mean_nuclei_metadata),
    ]


def make_cells_3d_sample_data() -> List["LayerData"]:
    all_data = cells3d()

    membrane_data = all_data[:, 0, :, :]
    membrane_metadata = _make_metadata(
        name="membrane",
        scale=(2, 1, 1),
        colormap="magenta",
        axis_names=("z", "y", "x"),
    )

    nuclei_data = all_data[:, 1, :, :]
    nuclei_metadata = _make_metadata(
        name="nuclei",
        scale=(2, 1, 1),
        colormap="green",
        axis_names=("z", "y", "x"),
    )

    return [
        (membrane_data, membrane_metadata),
        (nuclei_data, nuclei_metadata),
    ]


def _make_metadata(
    *,
    name: str,
    scale: Tuple[float, ...],
    colormap: str,
    axis_names: Tuple[str, ...],
) -> Dict:
    axes = [
        SpaceAxis(name=name, unit=SpaceUnits.MICROMETER) for name in axis_names
    ]
    original = OriginalMetadata(
        name=name,
        axes=tuple(deepcopy(axes)),
        scale=scale,
    )
    extras = ExtraMetadata(axes=axes, original=original)
    return {
        "name": name,
        "scale": scale,
        "colormap": colormap,
        "blending": "additive",
        "metadata": {EXTRA_METADATA_KEY: extras},
    }
