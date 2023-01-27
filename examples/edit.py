import napari

viewer = napari.Viewer()

viewer.axes.colored = False
viewer.axes.visible = True
viewer.scale_bar.visible = True

viewer.open_sample(plugin="napari-metadata", sample="cells-3d")
viewer.window.add_plugin_dock_widget(plugin_name="napari-metadata")

napari.run()
