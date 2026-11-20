def classFactory(iface):
    """Punto de entrada del plugin (QGIS 3.x y 4.x)."""
    from .freehand_plugin import FreehandDigitizePlugin
    return FreehandDigitizePlugin(iface)
