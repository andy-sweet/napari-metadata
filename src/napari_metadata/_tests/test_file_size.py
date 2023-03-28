from napari_metadata._file_size import generate_text_for_size


def test_generate_text_for_size():
    size = 13
    text = generate_text_for_size(size)
    assert text == '13.00 bytes'

    size = 130
    text = generate_text_for_size(size)
    assert text == '130.00 bytes'

    size = 1303
    text = generate_text_for_size(size)
    assert text == '1.30 KB'

    size = 13031
    text = generate_text_for_size(size)
    assert text == '13.03 KB'

    size = 130313
    text = generate_text_for_size(size)
    assert text == '130.31 KB'

    size = 1303131
    text = generate_text_for_size(size)
    assert text == '1.30 MB'

    size = 13031319
    text = generate_text_for_size(size)
    assert text == '13.03 MB'

    size = 130313190
    text = generate_text_for_size(size)
    assert text == '130.31 MB'

    size = 1303131900
    text = generate_text_for_size(size)
    assert text == '1.30 GB'


def test_generate_text_for_size_with_suffix():
    size = 13
    suffix = ' (in memory)'
    text = generate_text_for_size(size, suffix=suffix)
    assert text == f'13.00 bytes{suffix}'
