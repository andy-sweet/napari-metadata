from typing import List

from npe2.types import LayerData
from skimage.data import cells3d


def make_sample_data() -> List[LayerData]:
    all_data = cells3d()

    shared_metadata = {
        "scale": (2, 1, 1),
        "blending": "additive",
    }

    membrane_data = all_data[:, 0, :, :]
    membrane_metadata = dict(shared_metadata)
    membrane_metadata["colormap"] = "magenta"

    nuclei_data = all_data[:, 1, :, :]
    nuclei_metadata = dict(shared_metadata)
    nuclei_metadata["colormap"] = "green"

    return [
        (membrane_data, membrane_metadata),
        (nuclei_data, nuclei_metadata),
    ]
