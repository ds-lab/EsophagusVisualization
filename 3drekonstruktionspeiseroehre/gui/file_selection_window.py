import os
import pickle
import re
from pathlib import Path
from gui.visualization_window import VisualizationWindow
import numpy as np
import pandas as pd
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QMessageBox, QAction
from PyQt5 import uic
import config
from gui.master_window import MasterWindow
from gui.info_window import InfoWindow
from logic.visualization_data import VisualizationData

from gui.more_files import ShowMoreWindows
from gui.xray_region_selection_window import XrayRegionSelectionWindow


class FileSelectionWindow(QMainWindow):
    """Window where the user selects the needed files"""

    def __init__(self, master_window: MasterWindow):
        """
        init FileSelectionWindow
        :param master_window: the MasterWindow in which the next window will be displayed
        """
        super().__init__()
        self.ui = uic.loadUi("/Users/Alicia/PycharmProjects/3drekonstruktionspeiseroehre_flex/3drekonstruktionspeiseroehre/ui-files/file_selection_window_design.ui", self)
        self.master_window: MasterWindow = master_window
        self.default_path = str(Path.home())
        self.endoscopy_filenames = []
        self.endoscopy_image_positions = []
        self.ui.import_button.clicked.connect(self.__import_button_clicked)
        self.ui.visualization_button.clicked.connect(self.__visualization_button_clicked)
        self.ui.csv_button.clicked.connect(self.__csv_button_clicked)
        self.ui.xray_button1.clicked.connect(self.__xray_button_clicked1)
        self.ui.xray_button2.clicked.connect(self.__xray_button_clicked2)
        self.ui.xray_button3.clicked.connect(self.__xray_button_clicked3)
        self.ui.xray_button4.clicked.connect(self.__xray_button_clicked4)
        self.ui.xray_button5.clicked.connect(self.__xray_button_clicked5)
        self.ui.xray_button6.clicked.connect(self.__xray_button_clicked6)
        self.ui.xray_button7.clicked.connect(self.__xray_button_clicked7)
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

        visualization_list = [None, None, None, None, None, None, None]

        if len(self.ui.csv_textfield.text()) > 0 and (
                len(self.ui.xray_textfield1.text()) > 0 or len(self.ui.xray_textfield2.text()) > 0 or
                len(self.ui.xray_textfield3.text()) > 0 or len(self.ui.xray_textfield4.text()) > 0 or
                len(self.ui.xray_textfield5.text()) > 0 or len(self.ui.xray_textfield6.text()) > 0 or
                len(self.ui.xray_textfield7.text()) > 0):

            if len(self.ui.xray_textfield1.text()) > 0:
                visualization_data1 = VisualizationData()
                visualization_data1.xray_filename = self.ui.xray_textfield1.text()
                visualization_data1.pressure_matrix = self.pressure_matrix
                visualization_data1.endoscopy_filenames = self.endoscopy_filenames
                visualization_data1.endoscopy_image_positions_cm = self.endoscopy_image_positions
                visualization_list[0] = visualization_data1

            if len(self.ui.xray_textfield2.text()) > 0:
                visualization_data2 = VisualizationData()
                visualization_data2.xray_filename = self.ui.xray_textfield2.text()
                visualization_data2.pressure_matrix = self.pressure_matrix
                visualization_data2.endoscopy_filenames = self.endoscopy_filenames
                visualization_data2.endoscopy_image_positions_cm = self.endoscopy_image_positions
                visualization_list[1] = visualization_data2

            if len(self.ui.xray_textfield3.text()) > 0:
                visualization_data3 = VisualizationData()
                visualization_data3.xray_filename = self.ui.xray_textfield3.text()
                visualization_data3.pressure_matrix = self.pressure_matrix
                visualization_data3.endoscopy_filenames = self.endoscopy_filenames
                visualization_data3.endoscopy_image_positions_cm = self.endoscopy_image_positions
                visualization_list[2] = visualization_data3

            if len(self.ui.xray_textfield4.text()) > 0:
                visualization_data4 = VisualizationData()
                visualization_data4.xray_filename = self.ui.xray_textfield4.text()
                visualization_data4.pressure_matrix = self.pressure_matrix
                visualization_data4.endoscopy_filenames = self.endoscopy_filenames
                visualization_data4.endoscopy_image_positions_cm = self.endoscopy_image_positions
                visualization_list[3] = visualization_data4

            if len(self.ui.xray_textfield5.text()) > 0:
                visualization_data5 = VisualizationData()
                visualization_data5.xray_filename = self.ui.xray_textfield5.text()
                visualization_data5.pressure_matrix = self.pressure_matrix
                visualization_data5.endoscopy_filenames = self.endoscopy_filenames
                visualization_data5.endoscopy_image_positions_cm = self.endoscopy_image_positions
                visualization_list[4] = visualization_data5

            if len(self.ui.xray_textfield6.text()) > 0:
                visualization_data6 = VisualizationData()
                visualization_data6.xray_filename = self.ui.xray_textfield6.text()
                visualization_data6.pressure_matrix = self.pressure_matrix
                visualization_data6.endoscopy_filenames = self.endoscopy_filenames
                visualization_data6.endoscopy_image_positions_cm = self.endoscopy_image_positions
                visualization_list[5] = visualization_data6

            if len(self.ui.xray_textfield7.text()) > 0:
                visualization_data7 = VisualizationData()
                visualization_data7.xray_filename = self.ui.xray_textfield7.text()
                visualization_data7.pressure_matrix = self.pressure_matrix
                visualization_data7.endoscopy_filenames = self.endoscopy_filenames
                visualization_data7.endoscopy_image_positions_cm = self.endoscopy_image_positions
                visualization_list[6] = visualization_data7

            ShowMoreWindows(self.master_window, visualization_list)

        elif len(self.ui.import_textfield.text()) > 0:
            # Open the pickle file in binary mode for reading
            with open(self.ui.import_textfield.text(), 'rb') as file:
                # Load the VisualizationData object from import file
                visualization_data = pickle.load(file)
            visualization_window = VisualizationWindow(self.master_window, visualization_data)
            self.master_window.switch_to(visualization_window)
            self.close()

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
            except:
                error = True
            if error or self.pressure_matrix.shape[1] < 1:
                self.ui.csv_textfield.setText("")
                QMessageBox.critical(self, "Ungültige Datei", "Fehler: Die Datei hat nicht das erwartete Format")
            else:
                self.ui.csv_textfield.setText(filename)
        self.__check_button_activate()
        self.default_path = os.path.dirname(filename)

    def __xray_button_clicked1(self):
        """
        x-ray button callback
        """
        filename, _ = QFileDialog.getOpenFileName(self, 'Datei auswählen', self.default_path,
                                                  "Bilder (*.jpg *.JPG *.png *.PNG)")
        self.ui.xray_textfield1.setText(filename)
        self.__check_button_activate()
        self.default_path = os.path.dirname(filename)

    def __xray_button_clicked2(self):
        """
        x-ray button callback
        """
        filename, _ = QFileDialog.getOpenFileName(self, 'Datei auswählen', self.default_path,
                                                  "Bilder (*.jpg *.JPG *.png *.PNG)")
        self.ui.xray_textfield2.setText(filename)
        self.__check_button_activate()
        self.default_path = os.path.dirname(filename)

    def __xray_button_clicked3(self):
        """
        x-ray button callback
        """
        filename, _ = QFileDialog.getOpenFileName(self, 'Datei auswählen', self.default_path,
                                                  "Bilder (*.jpg *.JPG *.png *.PNG)")
        self.ui.xray_textfield3.setText(filename)
        self.__check_button_activate()
        self.default_path = os.path.dirname(filename)

    def __xray_button_clicked4(self):
        """
        x-ray button callback
        """
        filename, _ = QFileDialog.getOpenFileName(self, 'Datei auswählen', self.default_path,
                                                  "Bilder (*.jpg *.JPG *.png *.PNG)")
        self.ui.xray_textfield4.setText(filename)
        self.__check_button_activate()
        self.default_path = os.path.dirname(filename)

    def __xray_button_clicked5(self):
        """
        x-ray button callback
        """
        filename, _ = QFileDialog.getOpenFileName(self, 'Datei auswählen', self.default_path,
                                                  "Bilder (*.jpg *.JPG *.png *.PNG)")
        self.ui.xray_textfield5.setText(filename)
        self.__check_button_activate()
        self.default_path = os.path.dirname(filename)

    def __xray_button_clicked6(self):
        """
        x-ray button callback
        """
        filename, _ = QFileDialog.getOpenFileName(self, 'Datei auswählen', self.default_path,
                                                  "Bilder (*.jpg *.JPG *.png *.PNG)")
        self.ui.xray_textfield6.setText(filename)
        self.__check_button_activate()
        self.default_path = os.path.dirname(filename)

    def __xray_button_clicked7(self):
        """
        x-ray button callback
        """
        filename, _ = QFileDialog.getOpenFileName(self, 'Datei auswählen', self.default_path,
                                                  "Bilder (*.jpg *.JPG *.png *.PNG)")
        self.ui.xray_textfield7.setText(filename)
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

    def __import_button_clicked(self):
        """
        x-ray button callback
        """
        filename, _ = QFileDialog.getOpenFileName(self, 'Datei auswählen', self.default_path,
                                                  "exportierte Datei (*.pickle)")
        self.ui.import_textfield.setText(filename)
        self.__check_button_activate()
        self.default_path = os.path.dirname(filename)

    def __check_button_activate(self):
        """
        activates visualization button if necessary files are selected
        """
        if (len(self.ui.csv_textfield.text()) > 0 and (len(self.ui.xray_textfield1.text()) > 0 or
                                                       len(self.ui.xray_textfield2.text()) > 0 or
                                                       len(self.ui.xray_textfield5.text()) > 0) or
                len(self.ui.import_textfield.text()) > 0):
            self.ui.visualization_button.setDisabled(False)
        else:
            self.ui.visualization_button.setDisabled(True)
