"""QGIS-agnostic logic for the Freehand Digitize plugin.

Modules in this package must not import ``qgis``, ``qgis.gui`` or Qt: the GUI
layer converts QGIS objects into plain Python values before calling them.
"""

from __future__ import annotations
