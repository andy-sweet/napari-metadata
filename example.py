import napari

viewer = napari.Viewer()

viewer.axes.colored = False
viewer.axes.visible = True
viewer.scale_bar.visible = True

viewer.open_sample(plugin="napari-metadata", sample="cells3d")

napari.run()
