# Headless QGIS image for the integration suite.
# QGIS, PyQt and GDAL come from the official image; the plugin has no runtime
# Python dependencies, so no pip/uv install is needed inside the container.
FROM qgis/qgis:latest

ENV DEBIAN_FRONTEND=noninteractive
ENV QT_QPA_PLATFORM=offscreen
ENV REQUIRE_QGIS=1
ENV PYTHONPATH=/app:/usr/share/qgis/python

WORKDIR /app/freehand_digitize

COPY . .

CMD ["python3", "tests/run_integration.py"]
