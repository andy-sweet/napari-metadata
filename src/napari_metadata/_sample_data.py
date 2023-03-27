import os
from copy import deepcopy
from typing import TYPE_CHECKING, Dict, List, Tuple

import numpy as np
import pooch
from skimage.data import cells3d

from napari_metadata._model import (
    EXTRA_METADATA_KEY,
    ExtraMetadata,
    OriginalMetadata,
    SpaceAxis,
    SpaceUnits,
)
from napari_metadata._reader import napari_get_reader

if TYPE_CHECKING:
    from npe2.types import LayerData


def read_ome_zarr_hipsc_mip() -> List["LayerData"]:
    unzip_dir = pooch.retrieve(
        url="https://zenodo.org/record/7674571/files/"
        "20200812-CardiomyocyteDifferentiation14-Cycle1_mip.zarr.zip?"
        "download=1",
        known_hash="md5:93722285708d58a36a0a3ee413b2c8a1",
        processor=pooch.Unzip(),
        progressbar=True,
    )
    zarr_dir = os.path.split(unzip_dir[0])[0]
    reader = napari_get_reader(zarr_dir)
    return reader(zarr_dir)


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
        translate=(0,) * len(scale),
    )
    extras = ExtraMetadata(axes=axes, original=original)
    return {
        "name": name,
        "scale": scale,
        "colormap": colormap,
        "blending": "additive",
        "metadata": {EXTRA_METADATA_KEY: extras},
    }
