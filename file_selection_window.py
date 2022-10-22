import os
import re
from pathlib import Path
import numpy as np
import pandas as pd
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QMessageBox, QAction
from PyQt5 import uic
import config
from master_window import MasterWindow
from info_window import InfoWindow
from visualization_data import VisualizationData
from xray_region_selection_window import XrayRegionSelectionWindow


class FileSelectionWindow(QMainWindow):
    """Window where the user selects the needed files"""

    def __init__(self, master_window: MasterWindow):
        """
        init FileSelectionWindow
        :param master_window: the MasterWindow in which the next window will be displayed
        """
        super().__init__()
        self.ui = uic.loadUi("ui-files/file_selection_window_design.ui", self)
        self.master_window = master_window
        self.default_path = str(Path.home())
        self.endoscopy_filenames = []
        self.endoscopy_image_positions = []
        self.ui.visualization_button.clicked.connect(self.__visualization_button_clicked)
        self.ui.csv_button.clicked.connect(self.__csv_button_clicked)
        self.ui.xray_button.clicked.connect(self.__xray_button_clicked)
        self.ui.endoscopy_button.clicked.connect(self.__endoscopy_button_clicked)
        menu_button = QAction("Info", self)
        menu_button.triggered.connect(self.__menu_button_clicked)
        self.ui.menubar.addAction(menu_button)
        self.__check_button_activate()

    def __menu_button_clicked(self):
        """
        info button callback
        """
        info_window = InfoWindow()
        info_window.show_file_selection_info()
        info_window.show()

    def __visualization_button_clicked(self):
        """
        visualization button callback
        """
        visualization_data = VisualizationData()
        visualization_data.xray_filename = self.ui.xray_textfield.text()
        visualization_data.pressure_matrix = self.pressure_matrix
        visualization_data.endoscopy_filenames = self.endoscopy_filenames
        visualization_data.endoscopy_image_positions_cm = self.endoscopy_image_positions
        xray_selection_window = XrayRegionSelectionWindow(self.master_window, visualization_data)
        self.master_window.switch_to(xray_selection_window)
        self.close()

    def __csv_button_clicked(self):
        """
        csv button callback
        """
        filename, _ = QFileDialog.getOpenFileName(self, 'Datei auswählen', self.default_path, "CSV (*.csv *.CSV)")
        if len(filename) > 0:
            error = False
            try:
                df = pd.read_csv(filename, skiprows=config.csv_skiprows, header=0, index_col=0)
                df = df.drop(config.csv_drop_columns, axis=1)
                matrix = df.to_numpy()
                matrix = matrix.T  # sensors in axis 0
                self.pressure_matrix = np.flipud(matrix)  # sensors from top to bottom
            except KeyError:
                error = True
            if error or self.pressure_matrix.shape[1] < 1:
                self.ui.csv_textfield.setText("")
                QMessageBox.critical(self, "Ungültige Datei", "Fehler: Die Datei hat nicht das erwartete Format")
            else:
                self.ui.csv_textfield.setText(filename)
        self.__check_button_activate()
        self.default_path = os.path.dirname(filename)

    def __xray_button_clicked(self):
        """
        x-ray button callback
        """
        filename, _ = QFileDialog.getOpenFileName(self, 'Datei auswählen', self.default_path,
                                                  "Bilder (*.jpg *.JPG *.png *.PNG)")
        self.ui.xray_textfield.setText(filename)
        self.__check_button_activate()
        self.default_path = os.path.dirname(filename)

    def __endoscopy_button_clicked(self):
        """
        endoscopy button callback
        """
        filenames, _ = QFileDialog.getOpenFileNames(self, 'Dateien auswählen', self.default_path,
                                                    "Bilder (*.jpg *.JPG *.png *.PNG)")
        positions = []
        error = False
        for filename in filenames:
            match = re.search(r'_(?P<pos>[0-9]+)cm', filename)
            if match:
                positions.append(int(match.group('pos')))
            else:
                error = True
                QMessageBox.critical(self, "Ungültiger Dateiname", "Fehler: Der Dateiname der Datei '" + filename +
                                     "' enthält nicht die nötige Positionsangabe z.B. 'name_10cm.png' " +
                                     "(Format: Unterstrich + Ganzzahl + cm)")
                break
        if not error:
            self.ui.endoscopy_textfield.setText(str(len(filenames)) + " Dateien ausgewählt")
            self.endoscopy_image_positions = positions
            self.endoscopy_filenames = filenames

    def __check_button_activate(self):
        """
        activates visualization button if necessary files are selected
        """
        if len(self.ui.csv_textfield.text()) > 0 and len(self.ui.xray_textfield.text()) > 0:
            self.ui.visualization_button.setDisabled(False)
        else:
            self.ui.visualization_button.setDisabled(True)
