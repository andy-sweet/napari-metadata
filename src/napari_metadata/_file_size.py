from pathlib import Path
import os
import math
import logging
logger = logging.getLogger()


def magnitude(x):
    """Get the order of magnitude of a number.
    
    Parameters
    ----------
    x: int | float
        Number to determine magnitude. Must be >=0.
    
    Returns
    -------
    int: order of magnitude
    """
    if x == 0:
        return int(0)
    else:
        return int(math.log10(x))


def generate_text_for_size(size, suffix=''):
    """Generate the text for the file size widget. Consumes size in bytes, 
    reduces the order of magnitude and appends the units. Optionally adds 
    an addition suffix to the end of the string.

    >>> generate_text_for_size(1303131, suffix=' (in memory)')
    '1.30 MB (in memory)'


    Parameters
    ---------
    size: (int | float)
        The size in bytes
    suffix : (str, optional):
        Addition text suffix to add to the display. Defaults to ''.

    Returns:
        str: formatted text string for the file size
    """
    order = magnitude(size)
    logger.debug(f'order: {order}')
    if order <= 2:
        text = f'{size:.2f} bytes'
    elif order >= 3 and order < 6:
        text = f'{size / (10**3):.2f} KB'
    elif order >= 6 and order < 9:
        text = f'{size / 10**6:.2f} MB'
    else:
        text = f'{size / 10**9:.2f} GB'
    return f'{text}{suffix}'


def generate_display_size(layer):
    """High level generator for the displayed file size text on the widget. 
    If the provided layer has a source path, it will read the memory size on
    disk. If there is no source path on the layer, it will use the size of 
    the data array.

    Parameters
    ----------
    layer: napari.Layer
        Napari Layer for which to generate file size text

    Returns
    -------
    str: Formatted string for the file size or size in memory of the data. 
    """
    # data exist in file on disk
    if layer.source.path:
        size = os.path.getsize(str(layer.source.path))
        suffix = ''
    # data exists only in memory
    else:
        if type(layer).__name__ == 'Shapes' or type(layer).__name__ == 'Surface':
            size = 0 
            for shape in layer.data:
                size += shape.nbytes
        else:
            size = layer.data.nbytes
        suffix = ' (in memory)'
    text = generate_text_for_size(size, suffix=suffix)

    return text
