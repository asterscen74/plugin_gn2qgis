# -*- coding: utf-8 -*-

# Standard lib
from html import unescape

# PyQt libs
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor

# QGIS lib
from qgis.gui import QgsMapTool, QgsMapMouseEvent, QgsRubberBand
from qgis.core import (QgsGeometry,
                       QgsPointXY,
                       QgsWkbTypes,
                       QgsCoordinateReferenceSystem,
                       QgsCoordinateTransform,
                       QgsRectangle,
                       )


class RectangleDrawTool(QgsMapTool):
    signal = pyqtSignal()

    def __init__(self, project, canvas, crs):
        super().__init__(canvas)

        self.signal.connect(self.deactivate)

        self.project = project
        self.canvas = canvas
        self.crs = crs
        self.start_point = None
        self.end_point = None
        self.new_extent = None

        # flag to check if the left mouse button was pressed
        self.is_left_button_pressed = False
        # create a rubber line object
        # to display the geometry of the dragged object on the canvas
        self.rubber_band = QgsRubberBand(self.canvas, QgsWkbTypes.PolygonGeometry)
        self.rubber_band.setColor(QColor(255, 0, 0, 50))
        self.rubber_band.setWidth(2)

    # Mouse button pressed.
    def canvasPressEvent(self, event: QgsMapMouseEvent):
        if event.button() == Qt.LeftButton:
            self.start_point = self.toMapCoordinates(event.pos())
            self.end_point = self.start_point
            self.is_left_button_pressed = True
            if self.rubber_band:
                self.rubber_band.reset()

    # The cursor moves across the screen.
    def canvasMoveEvent(self, event: QgsMapMouseEvent):
        # if the left mouse button is pressed
        if self.is_left_button_pressed:
            self.end_point = self.toMapCoordinates(event.pos())
            # draw a rectangle on the canvas
            self.showRect(self.start_point, self.end_point)

    # The mouse button is released.
    def canvasReleaseEvent(self, event: QgsMapMouseEvent):
        # if the left mouse button was released
        if event.button() == Qt.LeftButton:
            self.new_extent = self.rectangle()
            self.signal.emit()
        # toggle the flag, the left mouse button is no longer held down
        self.is_left_button_pressed = False

    def showRect(self, startPoint, endPoint):
        # Reset the last rectangle
        self.rubber_band.reset(QgsWkbTypes.PolygonGeometry)
        # Only a rectangle can be used
        if startPoint.x() == endPoint.x() or startPoint.y() == endPoint.y():
            return

        point1 = QgsPointXY(startPoint.x(), startPoint.y())
        point2 = QgsPointXY(startPoint.x(), endPoint.y())
        point3 = QgsPointXY(endPoint.x(), endPoint.y())
        point4 = QgsPointXY(endPoint.x(), startPoint.y())

        self.rubber_band.addPoint(point1, False)
        self.rubber_band.addPoint(point2, False)
        self.rubber_band.addPoint(point3, False)
        self.rubber_band.addPoint(point4, True)  # true to update canvas
        self.rubber_band.show()

    def rectangle(self):
        # Only a rectangle is accepted
        if self.start_point is None or self.end_point is None:
            self.rubber_band = None
            return None
        elif (
                self.start_point.x() == self.end_point.x()
                or self.start_point.y() == self.end_point.y()
        ):
            self.rubber_band = None
            return None
        else:
            # Rectangle reprojection
            if str(self.project.instance().crs().postgisSrid()) != str(self.crs):
                start_point = self.transform_geom(
                    QgsGeometry().fromPointXY(self.start_point),
                    self.project.instance().crs(),
                    QgsCoordinateReferenceSystem("EPSG:" + str(self.crs)),
                )
                self.start_point = QgsPointXY(
                    start_point.asPoint().x(), start_point.asPoint().y()
                )
                end_point = self.transform_geom(
                    QgsGeometry().fromPointXY(self.end_point),
                    self.project.instance().crs(),
                    QgsCoordinateReferenceSystem("EPSG:" + str(self.crs)),
                )
                self.end_point = QgsPointXY(
                    end_point.asPoint().x(), end_point.asPoint().y()
                )
            return QgsRectangle(self.start_point, self.end_point)

    def transform_geom(self, geom, input_crs, output_crs):
        # Function used to reproject a geometry
        geom.transform(
            QgsCoordinateTransform(
                input_crs,
                output_crs,
                self.project,
            )
        )
        return geom

    def deactivate(self):
        # Signal to put the window on top when drawing the rectangle is over.
        pass

