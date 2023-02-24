from napari_metadata._file_size import generate_text_for_size


def test_generate_text_for_size():
    size = 13
    text = generate_text_for_size(size)
    assert text == f'13 bytes'

    size = 130
    text = generate_text_for_size(size)
    assert text == f'130 bytes'

    size = 1303
    text = generate_text_for_size(size)
    assert text == f'1.303 KB'

    size = 13031
    text = generate_text_for_size(size)
    assert text == f'13.031 KB'

    size = 130313
    text = generate_text_for_size(size)
    assert text == f'130.313 KB'

    size = 1303131
    text = generate_text_for_size(size)
    assert text == f'1.303131 MB'

    size = 13031319
    text = generate_text_for_size(size)
    assert text == f'13.031319 MB'

    size = 130313190
    text = generate_text_for_size(size)
    assert text == f'130.31319 MB'

    size = 1303131900
    text = generate_text_for_size(size)
    assert text == f'1.3031319 GB'
