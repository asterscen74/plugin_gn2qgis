# -*- coding: utf-8 -*-

# Standard libs
import json
from distutils.version import StrictVersion

# PyQt libs
from PyQt5.QtCore import QJsonDocument, QObject, pyqtSignal, QVariant, QThread
from PyQt5.QtNetwork import QNetworkReply, QNetworkRequest

# QGIS lib
from qgis.core import (
    QgsGeometry,
    QgsField,
    QgsVectorLayer,
    QgsPointXY,
    QgsFeature,
    QgsFeatureRequest,
)
from qgis.PyQt.Qt import QUrl

from gn2qgis.__about__ import (
    __geonature_version__,
    __geonature_crs__,
    __geonature_data__,
    __geonature_obs__,
)


class ImportData(QObject):
    finished_dl = pyqtSignal()
    """Get multiples informations from a getcapabilities request.
    List all layers available, get the maximal extent of all the Wfs' data."""

    def __init__(
        self,
        parent=None,
        extent=None,
        thread=None,
        complex_data=None,
    ):
        super().__init__()
        self.parent = parent
        self.extent = extent
        self.thread = thread
        self.complex_data = complex_data

        self.url = __geonature_data__
        self.site_crs = __geonature_crs__

        self.project = self.parent.project

        self.data = None

        self.point_id_number = 0
        self.point_layer = QgsVectorLayer("Point?crs=epsg:" + str(self.site_crs), "obs_pt", "memory")
        self.point_layer.startEditing()
        self.point_layer.addAttribute(QgsField("id", QVariant.Int, "integer", 10))
        self.point_layer.addAttribute(QgsField("cd_nom", QVariant.Int, "integer", 10))
        self.point_layer.addAttribute(QgsField("nom_scien", QVariant.String, "string", 254))
        self.point_layer.addAttribute(QgsField("nom_vern", QVariant.String, "string", 254))
        self.point_layer.addAttribute(QgsField("observat", QVariant.String, "string", 254))
        self.point_layer.addAttribute(QgsField("projet", QVariant.String, "string", 254))
        self.point_layer.addAttribute(QgsField("date", QVariant.String, "string", 254))
        self.point_layer.addAttribute(QgsField("effectif", QVariant.Int, "integer", 10))
        self.point_layer.commitChanges()
        self.point_layer.triggerRepaint()

        id_number = 0
        self.line_id_number = 0
        self.line_layer = QgsVectorLayer("LineString?crs=epsg:" + str(self.site_crs), "line_obs", "memory")
        self.line_layer.startEditing()
        self.line_layer.addAttribute(QgsField("id", QVariant.Int, "integer", 10))
        self.line_layer.addAttribute(QgsField("cd_nom", QVariant.Int, "integer", 10))
        self.line_layer.addAttribute(QgsField("nom_scien", QVariant.String, "string", 254))
        self.line_layer.addAttribute(QgsField("nom_vern", QVariant.String, "string", 254))
        self.line_layer.addAttribute(QgsField("observat", QVariant.String, "string", 254))
        self.line_layer.addAttribute(QgsField("projet", QVariant.String, "string", 254))
        self.line_layer.addAttribute(QgsField("date", QVariant.String, "string", 254))
        self.line_layer.addAttribute(QgsField("effectif", QVariant.Int, "integer", 10))
        self.line_layer.addAttribute(QgsField("longueur", QVariant.Double, "float", 10, 3))
        self.line_layer.commitChanges()
        self.line_layer.triggerRepaint()


        self.polygon_id_number = 0
        self.polygon_layer = QgsVectorLayer("MultiPolygon?crs=epsg:" + str(self.site_crs), "multipolygon_obs", "memory")
        self.polygon_layer.startEditing()
        self.polygon_layer.addAttribute(QgsField("id", QVariant.Int, "integer", 10))
        self.polygon_layer.addAttribute(QgsField("cd_nom", QVariant.Int, "integer", 10))
        self.polygon_layer.addAttribute(QgsField("nom_scien", QVariant.String, "string", 254))
        self.polygon_layer.addAttribute(QgsField("nom_vern", QVariant.String, "string", 254))
        self.polygon_layer.addAttribute(QgsField("observat", QVariant.String, "string", 254))
        self.polygon_layer.addAttribute(QgsField("projet", QVariant.String, "string", 254))
        self.polygon_layer.addAttribute(QgsField("date", QVariant.String, "string", 254))
        self.polygon_layer.addAttribute(QgsField("effectif", QVariant.Int, "integer", 10))
        self.polygon_layer.addAttribute(QgsField("surface", QVariant.Double, "float", 10, 3))
        self.polygon_layer.commitChanges()
        self.polygon_layer.triggerRepaint()

        self._pending_downloads = 0

        self.download()

    @property
    def pending_downloads(self):
        return self._pending_downloads

    @property
    def pending_features(self):
        return self._pending_features

    def download(self):
        url = QUrl(self.url)
        request = QNetworkRequest(url)
        request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")

        if StrictVersion(__geonature_version__) > StrictVersion("2.13.0"):
            json_data = {"modif_since_validation": 'false',
                        "geoIntersection": {"type": "Feature",
                                            "properties": {},
                                            "geometry": json.loads(QgsGeometry().fromRect(self.extent).asJson())
                                            }
                        }
        else:
            print(__geonature_version__)
            json_data = {"with_areas": 'false',
                        "geoIntersection": QgsGeometry().fromRect(self.extent).asWkt()
                        }
        print(json_data)
        document = QJsonDocument(json_data)
        reply = self.parent.network_manager.post(request, document.toJson())
        reply.finished.connect(lambda: self.handle_finished(reply))
        self._pending_downloads += 1

    def handle_finished(self, reply):
        self._pending_downloads -= 1
        if reply.error() != QNetworkReply.NoError:
            print(f"code: {reply.error()} message: {reply.errorString()}")
        else:
            data_request = reply.readAll().data().decode()
            if data_request != "":
                self.data = json.loads(data_request)
                self._pending_features = len(self.data["features"])
                self.thread.set_max(self.pending_features)
                if self.complex_data:
                    self.download_obs_properties(self.data["features"][self._pending_features - 1])
                else:
                    self.download_obs()

    def add_feature_to_layer(self, attributes):
        if attributes["geometry_type"] == 'Point':
            point = QgsGeometry.fromPointXY(QgsPointXY(attributes["geometry"][0], attributes["geometry"][1]))
            feature = QgsFeature(self.point_layer.fields())
            feature.setGeometry(point)
            feature.setAttribute(0, self.point_id_number)
            feature.setAttribute(1, attributes["cd_nom"])
            feature.setAttribute(2, attributes["lb_nom"])
            feature.setAttribute(3, attributes["nom_cite"])
            feature.setAttribute(4, attributes["observers"])
            feature.setAttribute(5, attributes["dataset"])
            feature.setAttribute(6, attributes["date_min"])
            feature.setAttribute(7, attributes["count_min"])
            self.point_id_number = self.point_id_number + 1
            point_provider = self.point_layer.dataProvider()
            point_provider.addFeatures([feature])
            self.point_layer.updateExtents()
        elif attributes["geometry_type"] == 'MultiPoint':
            for coords in attributes["geometry"]:
                x = coords[0]
                y = coords[1]
                point = QgsGeometry.fromPointXY(QgsPointXY(x, y))
                feature = QgsFeature(self.point_layer.fields())
                feature.setGeometry(point)
                feature.setAttribute(0, self.point_id_number)
                feature.setAttribute(1, attributes["cd_nom"])
                feature.setAttribute(2, attributes["lb_nom"])
                feature.setAttribute(3, attributes["nom_cite"])
                feature.setAttribute(4, attributes["observers"])
                feature.setAttribute(5, attributes["dataset"])
                feature.setAttribute(6, attributes["date_min"])
                feature.setAttribute(7, attributes["count_min"])
                point_provider = self.point_layer.dataProvider()
                point_provider.addFeatures([feature])
                self.point_layer.updateExtents()
                self.point_id_number = self.point_id_number + 1
        elif attributes["geometry_type"] == 'LineString':
            line = QgsGeometry.fromPolylineXY([QgsPointXY(pair[0], pair[1]) for pair in attributes["geometry"]])
            feature = QgsFeature(self.line_layer.fields())
            feature.setGeometry(line)
            feature.setAttribute(0, self.line_id_number)
            feature.setAttribute(1, attributes["cd_nom"])
            feature.setAttribute(2, attributes["lb_nom"])
            feature.setAttribute(3, attributes["nom_cite"])
            feature.setAttribute(4, attributes["observers"])
            feature.setAttribute(5, attributes["dataset"])
            feature.setAttribute(6, attributes["date_min"])
            feature.setAttribute(7, attributes["count_min"])
            feature.setAttribute(8, line.length())
            line_provider = self.line_layer.dataProvider()
            line_provider.addFeatures([feature])
            self.line_layer.updateExtents()
            self.line_id_number = self.line_id_number + 1
        elif attributes["geometry_type"] == 'Polygon':
            line = QgsGeometry.fromPolylineXY(
                [QgsPointXY(pair[0], pair[1]) for pair in attributes["geometry"][0]])
            polygon = QgsGeometry.fromPolygonXY([line.asPolyline()])
            feature = QgsFeature(self.polygon_layer.fields())
            feature.setGeometry(polygon)
            feature.setAttribute(0, self.polygon_id_number)
            feature.setAttribute(1, attributes["cd_nom"])
            feature.setAttribute(2, attributes["lb_nom"])
            feature.setAttribute(3, attributes["nom_cite"])
            feature.setAttribute(4, attributes["observers"])
            feature.setAttribute(5, attributes["dataset"])
            feature.setAttribute(6, attributes["date_min"])
            feature.setAttribute(7, attributes["count_min"])
            feature.setAttribute(8, polygon.area())
            polygon_provider = self.polygon_layer.dataProvider()
            polygon_provider.addFeatures([feature])
            self.polygon_layer.updateExtents()
            self.polygon_id_number = self.polygon_id_number + 1
        elif attributes["geometry_type"] == 'MultiPolygon':
            polygon = QgsGeometry.fromMultiPolygonXY(
                [[[QgsPointXY(pair[0], pair[1]) for pair in attributes["geometry"][0][0]]]])
            feature = QgsFeature(self.polygon_layer.fields())
            feature.setGeometry(polygon)
            feature.setAttribute(0, self.polygon_id_number)
            feature.setAttribute(1, attributes["cd_nom"])
            feature.setAttribute(2, attributes["lb_nom"])
            feature.setAttribute(3, attributes["nom_cite"])
            feature.setAttribute(4, attributes["observers"])
            feature.setAttribute(5, attributes["dataset"])
            feature.setAttribute(6, attributes["date_min"])
            feature.setAttribute(7, attributes["count_min"])
            feature.setAttribute(8, polygon.area())
            polygon_provider = self.polygon_layer.dataProvider()
            polygon_provider.addFeatures([feature])
            self.polygon_layer.updateExtents()
            self.polygon_id_number = self.polygon_id_number + 1
        else:
            print(attributes["geometry_type"])
            print(attributes["geometry"])



    def download_obs(self):
        for obs in self.data["features"]:
            if StrictVersion(__geonature_version__) > StrictVersion("2.13.0"):
                if obs["geometry"]["type"] == "MultiPoint":
                    print(obs)
                attributes = {"geometry_type": obs["geometry"]["type"],
                            "geometry": obs["geometry"]["coordinates"],
                            "cd_nom": None,
                            "lb_nom": obs["properties"]["lb_nom"],
                            "nom_cite": None,
                            "observers": obs["properties"]["observers"],
                            "dataset": obs["properties"]['dataset_name'],
                            "date_min": obs["properties"]["date_min"],
                            "count_min": None
                            }
            else:
                attributes = {"geometry_type": obs["geometry"]["type"],
                            "geometry": obs["geometry"]["coordinates"],
                            "cd_nom": None,
                            "lb_nom": obs["properties"]["observations"][0]["lb_nom"],
                            "nom_cite": None,
                            "observers": obs["properties"]["observations"][0]["observers"],
                            "dataset": obs["properties"]["observations"][0]['dataset_name'],
                            "date_min": obs["properties"]["observations"][0]["date_min"],
                            "count_min": None
                            } 
            self.add_feature_to_layer(attributes)
            self.thread.add_one()
            self._pending_features -= 1
        self.thread.finish()
        self.thread.reset_value()
        self.project.addMapLayer(self.polygon_layer)
        self.polygon_layer.renderer().setOrderByEnabled(True)
        clause = QgsFeatureRequest.OrderByClause('surface', ascending=False)
        orderby = QgsFeatureRequest.OrderBy([clause])
        self.polygon_layer.renderer().setOrderBy(orderby)
        self.polygon_layer.triggerRepaint()
        self.project.addMapLayer(self.line_layer)
        self.project.addMapLayer(self.point_layer)
        print("FINISHED")
        self.finished_dl.emit()


    def download_obs_properties(self, obs):
        obs_id = obs['properties']['id']
        url = QUrl(__geonature_obs__ + "/" + str(obs_id))
        request = QNetworkRequest(url)
        request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")

        reply = self.parent.network_manager.get(request)
        reply.finished.connect(lambda: self.handle_obs(reply))

    def add_obs_to_layer(self, obs_properties):
        attributes = {"geometry_type": obs_properties["geometry"]["type"],
                      "geometry": obs_properties["geometry"]["coordinates"],
                      "cd_nom": obs_properties["properties"]["cd_nom"],
                      "lb_nom": obs_properties["properties"]["nom_cite"],
                      "nom_cite": obs_properties["properties"]["nom_cite"],
                      "observers": obs_properties["properties"]["observers"],
                      "dataset": obs_properties["properties"]['dataset']['dataset_name'],
                      "date_min": obs_properties["properties"]["date_min"],
                      "count_min": obs_properties["properties"]["count_min"]
                      }
        self.add_feature_to_layer(attributes)

    def handle_obs(self, reply):
        self.thread.add_one()
        self._pending_features -= 1
        if reply.error() != QNetworkReply.NoError:
            print(f"code: {reply.error()} message: {reply.errorString()}")
        else:
            data = json.loads(reply.readAll().data().decode())
            self.add_obs_to_layer(data)
            if self.pending_features != 0:
                self.download_obs_properties(self.data["features"][self._pending_features - 1])
            else:
                self.thread.finish()
                self.thread.reset_value()
                self.project.addMapLayer(self.polygon_layer)
                self.polygon_layer.renderer().setOrderByEnabled(True)
                clause = QgsFeatureRequest.OrderByClause('surface', ascending=False)
                orderby = QgsFeatureRequest.OrderBy([clause])
                self.polygon_layer.renderer().setOrderBy(orderby)
                self.polygon_layer.triggerRepaint()
                self.project.addMapLayer(self.line_layer)
                self.project.addMapLayer(self.point_layer)
                print("FINISHED")
                self.finished_dl.emit()
