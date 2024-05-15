# -*- coding: utf-8 -*-
# PyQt libs
from PyQt5.QtWidgets import (
                             QDialog,
                             QPushButton,
                             QGridLayout,
                             QCheckBox,
                             QVBoxLayout,
                             QButtonGroup,
                             QLabel,
                             QProgressBar,)
from PyQt5.QtCore import QThread, pyqtSignal

# QGIS lib
from qgis.gui import QgsMapLayerComboBox
from qgis.core import QgsMapLayerProxyModel

# project
from gn2qgis.__about__ import (
    __geonature__,
    __geonature_data__,
    __geonature_crs__,
    __icon_path__,
    __title__,
    __uri_homepage__,
)
from gn2qgis.toolbelt.rectangle_draw import RectangleDrawTool
from gn2qgis.processing.import_data import ImportData


class DataSelection(QDialog):
    def __init__(self, parent, project, iface):
        """
        Constructor

        @param parent reference to the parent widget
        @type QDialog
        """
        QDialog.__init__(self)
        self.parent = parent
        self.project = project
        self.main_window = iface.mainWindow()
        self.canvas = iface.mapCanvas()
        
        self.data_url = __geonature_data__
        self.domain = __geonature__.split("//")[1]
        self.site_crs = __geonature_crs__
        self.set_rectangle_tool()

        self.nb_especes = 0
        self.nb_obs = 0
        self.species_list = []
        self.groupes_tuple = ()

        self.resize(600, 204)
        self.layout = QGridLayout()

        # Draw rectangle tool
        self.layout = QVBoxLayout()
        extent_check_group = QButtonGroup(self)
        extent_check_group.setExclusive(True)
        self.extent_layout = QGridLayout()
        layout_row_count = 0
        self.draw_rectangle_checkbox = QCheckBox(self)
        self.draw_rectangle_checkbox.setText(
            self.tr("Tracer une emprise pour extraire les données :")
        )
        self.draw_rectangle_checkbox.setChecked(True)
        extent_check_group.addButton(self.draw_rectangle_checkbox)
        self.extent_layout.addWidget(
            self.draw_rectangle_checkbox, layout_row_count, 0, 1, 2
        )

        self.draw_rectangle_button = QPushButton(self)
        self.draw_rectangle_button.setEnabled(True)
        self.draw_rectangle_button.clicked.connect(self.pointer)
        self.draw_rectangle_button.setText(self.tr("Tracer une emprise"))
        self.extent_layout.addWidget(
            self.draw_rectangle_button, layout_row_count, 2, 1, 3
        )
        layout_row_count = layout_row_count + 1

        # Select layer tool
        self.select_layer_checkbox = QCheckBox(self)
        self.select_layer_checkbox.setText(
            self.tr("Utiliser l'emprise d'une couche pour extraire les données :")
        )
        self.select_layer_checkbox.setChecked(False)
        extent_check_group.addButton(self.select_layer_checkbox)
        self.extent_layout.addWidget(
            self.select_layer_checkbox, layout_row_count, 0, 2, 2
        )

        self.select_layer_combo_box = QgsMapLayerComboBox(self)
        self.select_layer_combo_box.setFilters(
            QgsMapLayerProxyModel.PolygonLayer
            | QgsMapLayerProxyModel.LineLayer
            | QgsMapLayerProxyModel.RasterLayer
        )
        self.select_layer_combo_box.setEnabled(False)
        self.extent_layout.addWidget(
            self.select_layer_combo_box, layout_row_count, 2, 1, 3
        )
        self.layout.addLayout(self.extent_layout)

        self.select_option_checkbox = QCheckBox(self)
        self.select_option_checkbox.setText(
            self.tr("Avoir des données complètes (prend plus de temps) :")
        )
        self.select_option_checkbox.setChecked(False)
        self.layout.addWidget(self.select_option_checkbox)

         # Progress Bar
        self.select_progress_bar_label = QLabel(self)
        self.select_progress_bar_label.setText("")
        self.layout.addWidget(self.select_progress_bar_label)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)
        self.thread = Thread()
        self.thread._signal.connect(self.signal_accept)
        self.layout.addWidget(self.progress_bar)
        self.layout.insertSpacing(100, 25)

        # Button to validate the login and far_study_area_path.
        self.ok_button = QPushButton('OK', self)
        self.ok_button.clicked.connect(self.result)
        self.ok_button.setEnabled(False)
        self.layout.addWidget(self.ok_button)

        self.setLayout(self.layout)

        self.draw_rectangle_checkbox.stateChanged.connect(
            self.draw_rectangle_button.setEnabled
        )
        self.draw_rectangle_checkbox.stateChanged.connect(
            self.select_layer_combo_box.setDisabled
        )
        self.draw_rectangle_checkbox.stateChanged.connect(self.check_config)

        self.select_layer_checkbox.stateChanged.connect(
            self.select_layer_combo_box.setEnabled
        )
        self.select_layer_checkbox.stateChanged.connect(
            self.draw_rectangle_button.setDisabled
        )
        self.select_layer_checkbox.stateChanged.connect(
            self.erase_rubber_band
        )
        self.draw_rectangle_checkbox.stateChanged.connect(self.check_config)

    def signal_accept(self, msg):
        # Update the progress bar when result is pressed
        self.progress_bar.setValue(int(msg))
        if self.progress_bar.value() == 101:
            self.progress_bar.setValue(0)

    def check_config(self):
        if self.draw_rectangle_checkbox.isChecked():
            if self.rectangle_tool.rubber_band:
                self.ok_button.setEnabled(True)
            else:
                print("ERROR")
        elif self.select_layer_checkbox.isChecked():
            if self.select_layer_combo_box.currentLayer():
                self.ok_button.setEnabled(True)
            else:
                print("ERROR")
        else:
            print("ERROR")

    def set_rectangle_tool(self):
        self.rectangle_tool = RectangleDrawTool(self.project, self.canvas, self.site_crs)
        self.rectangle_tool.signal.connect(self.activate_window)

    def pointer(self):
        # Add the tool to draw a rectangle
        # self.setVisible(False)
        self.hide()
        self.canvas.setMapTool(self.rectangle_tool)

    def activate_window(self):
        # Put the dialog on top once the rectangle is drawn
        # self.canvas.unsetMapTool(self.rectangle_tool)
        self.show()
        self.check_config()

    def close_window(self):
        self.close()

    def erase_rubber_band(self):
        # Erase the drawn rectangle
        if self.rectangle_tool.rubber_band:
            self.rectangle_tool.rubber_band.reset()
        else:
            pass

    def get_data_from_geonature(self, extent):
        self.import_data = ImportData(self.parent, extent, self.thread, self.select_option_checkbox.isChecked())
        self.import_data.finished_dl.connect(self.close_window)

    def result(self):
        # Remove the map tool to draw the rectangle
        self.canvas.unsetMapTool(self.rectangle_tool)
        if self.draw_rectangle_checkbox.isChecked():
            extent = self.rectangle_tool.new_extent
            # Remove rectangle from map
            self.erase_rubber_band()
        elif self.select_layer_checkbox.isChecked():
            extent = self.select_layer_combo_box.currentLayer().extent()
        self.get_data_from_geonature(extent)

    def disconnect(self):
        if self.rectangle_tool:
            self.canvas.unsetMapTool(self.rectangle_tool)
            self.erase_rubber_band()

class Thread(QThread):
    """Thread used fot the ProgressBar"""

    _signal = pyqtSignal(int)

    def __init__(self):
        super(Thread, self).__init__()
        self.max_value = 1
        self.value = 0

    def __del__(self):
        self.wait()

    def set_max(self, max_value):
        self.max_value = max_value

    def add_one(self):
        self.value = self.value + 1
        self._signal.emit(int((self.value / self.max_value) * 100))

    def finish(self):
        self._signal.emit(101)

    def reset_value(self):
        self.value = 0
