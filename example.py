import napari

viewer = napari.Viewer()

viewer.axes.colored = False
viewer.axes.visible = True
viewer.scale_bar.visible = True

viewer.open_sample(plugin="napari-metadata", sample="cells3d")
viewer.window.add_plugin_dock_widget(plugin_name="napari-metadata")

viewer.dims.axis_labels = ("z", "y", "x")
viewer.scale_bar.unit = "um"

napari.run()
