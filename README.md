# napari-metadata

[![tests](https://github.com/andy-sweet/napari-metadata/workflows/tests/badge.svg)](https://github.com/andy-sweet/napari-metadata/actions)
[![codecov](https://codecov.io/gh/andy-sweet/napari-metadata/branch/main/graph/badge.svg)](https://codecov.io/gh/andy-sweet/napari-metadata)

This is a [napari] plugin that expands the functionality of napari's handling of layer metadata.
It exercises napari's existing metadata-related API to provide a GUI to inspect, control, read,
and write some key metadata attributes.

In its current form, this plugin is intended to be rough, not widely distributed, and not formally supported.
Instead I'm trying to understand how much napari can currently support some desired use cases around metadata.
After some amount of progress, the plan is to either pursue this as a fully fledged plugin or look for ways
to push related improvements upstream to napari and other metadata-related plugins.

Therefore, at the time of writing, I recommend not depending on this plugin and its code in this repository in any way.
If you have ideas or comments about this work, feel free to [file an issue].
I'll also try to track any efforts I'm currently working with issues.

## Installation

You can install the latest development version of `napari-metadata` via [pip]:

    pip install git+https://github.com/andy-sweet/napari-metadata.git

Alternatively, fork or clone this repository directly.

## Contributing

Contributions are not yet welcome because this is still very much a work in progress.
But that might change in the future!

## License

Distributed under the terms of the [BSD-3] license,
"napari-metadata" is free and open source software

## Issues

If you encounter any problems, please [file an issue] along with a detailed description.

[napari]: https://github.com/napari/napari
[BSD-3]: http://opensource.org/licenses/BSD-3-Clause
[file an issue]: https://github.com/andy-sweet/napari-metadata/issues
