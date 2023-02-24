from pathlib import Path
import os
import math


def get_filesize(path):
    size_bytes = os.path.getsize(str(path))
    return size_bytes


def magnitude(x):
    return int(math.log10(x))


def generate_text_for_size(size):
    order = magnitude(size)

    if order <= 2:
        text = f'{size} bytes'
    elif order >= 3 and order < 6:
        text = f'{size / (10**3)} KB'
    elif order >= 6 and order < 9:
        text = f'{size / 10**6} MB'
    else:
        text = f'{size / 10**9} GB'
    return text


def generate_display_size(path):
    size = get_filesize(path)
    text = generate_text_for_size(size)

    return text
