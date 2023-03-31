# napari-metadata

[![tests](https://github.com/andy-sweet/napari-metadata/workflows/tests/badge.svg)](https://github.com/andy-sweet/napari-metadata/actions)
[![codecov](https://codecov.io/gh/andy-sweet/napari-metadata/branch/main/graph/badge.svg)](https://codecov.io/gh/andy-sweet/napari-metadata)

This is a [napari] plugin that expands the functionality of napari's handling of layer metadata.

It uses napari's existing `Layer.metadata` dictionary to store some extra metadata attributes like layer specific axis names to provide a few contributions.

- A reader to read some metadata from OME-Zarr images.
- A writer to write some metadata to a multiscale OME-Zarr image.
- A widget to control the extra attributes and view some other important read-only attributes.
- Some sample data to demonstrate basic usage.

This plugin is still an experimental work in progress. As such, it is not widely distributed and you should not expect support or future maintenance.

This plugin lacks a public API by design. In particular, you should not rely on any of the extra keys or values in `Layer.metadata` in your own software of napari plugins. They are purely implementation details of this plugin.

You can of course feel free to use the plugin or any of its code, but by doing so accept ownership of any issues that arise. If you have ideas or comments about this work, feel free to [file an issue].

## Installation

You can install the latest development version of `napari-metadata` via [pip]:

    pip install git+https://github.com/andy-sweet/napari-metadata.git

Alternatively, fork or clone this repository directly.

## Contributing

Since this is still experimental, I don't encourage contributions and likely won't review PRs with much urgency.

## License

Distributed under the terms of the [BSD-3] license,
"napari-metadata" is free and open source software

## Issues

If you encounter any problems, please [file an issue] along with a detailed description.

[napari]: https://github.com/napari/napari
[BSD-3]: http://opensource.org/licenses/BSD-3-Clause
[file an issue]: https://github.com/andy-sweet/napari-metadata/issues
