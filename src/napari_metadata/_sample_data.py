from typing import TYPE_CHECKING, List

import numpy as np
from skimage.data import cells3d

if TYPE_CHECKING:
    from npe2.types import LayerData


def make_nuclei_md_sample_data() -> List["LayerData"]:
    all_data = cells3d()

    nuclei_data = all_data[:, 1, :, :]
    nuclei_metadata = {
        "name": "nuclei",
        "scale": (2, 1, 1),
        "colormap": "green",
        "blending": "additive",
    }

    mean_nuclei_data = np.mean(nuclei_data, axis=0)
    mean_nuclei_metadata = {
        "name": "nuclei_mean",
        "scale": (1, 1),
        "colormap": "blue",
        "blending": "additive",
    }

    return [
        (nuclei_data, nuclei_metadata),
        (mean_nuclei_data, mean_nuclei_metadata),
    ]


def make_cells_3d_sample_data() -> List["LayerData"]:
    all_data = cells3d()

    shared_metadata = {
        "scale": (2, 1, 1),
        "blending": "additive",
    }

    membrane_data = all_data[:, 0, :, :]
    membrane_metadata = dict(shared_metadata)
    membrane_metadata["name"] = "membrane"
    membrane_metadata["colormap"] = "magenta"

    nuclei_data = all_data[:, 1, :, :]
    nuclei_metadata = dict(shared_metadata)
    nuclei_metadata["name"] = "nuclei"
    nuclei_metadata["colormap"] = "green"

    return [
        (membrane_data, membrane_metadata),
        (nuclei_data, nuclei_metadata),
    ]
