import os
import pickle
import re
from pathlib import Path

import config
import gui.visualization_window
import numpy as np
import pandas as pd
from gui.info_window import InfoWindow
from gui.master_window import MasterWindow
from gui.xray_window_managment import ManageXrayWindows
from logic.endoflip_data_processing import process_endoflip_xlsx
from logic.patient_data import PatientData
from logic.visit_data import VisitData
from logic.visualization_data import VisualizationData
from PyQt5 import uic
from PyQt5.QtWidgets import QAction, QFileDialog, QMainWindow, QMessageBox


class FileSelectionWindow(QMainWindow):
    """Window where the user selects the needed files"""

    def __init__(self, master_window: MasterWindow, patient_data: PatientData = PatientData()):
        """
        init FileSelectionWindow
        :param master_window: the MasterWindow in which the next window will be displayed
        :param patient_data:
        """
        super().__init__()
        self.ui = uic.loadUi("3drekonstruktionspeiseroehre/ui-files/file_selection_window_design.ui", self)
        self.master_window: MasterWindow = master_window
        self.patient_data: PatientData = patient_data
        self.default_path = str(Path.home())
        self.import_filenames = []
        self.endoscopy_filenames = []
        self.xray_filenames = []
        self.endoscopy_image_positions = []
        self.endoflip_screenshot = None
        self.ui.import_button.clicked.connect(self.__import_button_clicked)
        self.ui.visualization_button.clicked.connect(self.__visualization_button_clicked)
        self.ui.csv_button.clicked.connect(self.__csv_button_clicked)
        self.ui.xray_button_all.clicked.connect(self.__xray_button_clicked_all)
        self.ui.endoscopy_button.clicked.connect(self.__endoscopy_button_clicked)
        self.ui.endoflip_button.clicked.connect(self.__endoflip_button_clicked)
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
        if len(self.ui.csv_textfield.text()) > 0 and len(self.ui.xray_textfield_all.text()) > 0:
            if len(self.ui.visualization_namefield.text()) > 0:
                    # Add name if user chooses to name the reconstruction
                    name = self.ui.visualization_namefield.text()
                    if self.ui.visualization_namefield.text() in self.patient_data.visit_data_dict.keys():
                        QMessageBox.critical(self, "Rekonstruktionsname nicht eindeutig","Fehler: Rekonstruktionsnamen müssen eindeutig sein.")
                        return
            else:
                    # No name was specifiied by user -> use pseudonym and xray filename
                    name = self.xray_filenames[0].split("/")[-3] + "-" + self.xray_filenames[0].split("/")[-1].split(".")[0]

            visit = VisitData(name)
            for xray_filename in self.xray_filenames:
                visualization_data = VisualizationData()
                visualization_data.xray_filename = xray_filename


                visualization_data.pressure_matrix = self.pressure_matrix
                visualization_data.endoflip_screenshot = self.endoflip_screenshot
                visualization_data.endoscopy_filenames = self.endoscopy_filenames
                visualization_data.endoscopy_image_positions_cm = self.endoscopy_image_positions
                visit.add_visualization(visualization_data)

            ManageXrayWindows(self.master_window, visit, self.patient_data)

        elif len(self.ui.import_textfield.text()) > 0:
            # Iterate over *.achalasie files
            for import_filename in self.import_filenames:
                 # Open the pickle file in binary mode for reading
                with open(import_filename, 'rb') as file:
                    # Load the VisualizationData object from import file and add it to patient_data
                    self.patient_data.add_visit(import_filename.split("/")[-1].split(".")[0], pickle.load(file))

            visualization_window = gui.visualization_window.VisualizationWindow(self.master_window, self.patient_data)
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


    def __xray_button_clicked_all(self):
        """
        x-ray button callback
        """
        filenames, _ = QFileDialog.getOpenFileNames(self, 'Dateien auswählen', self.default_path,
                                                  "Bilder (*.jpg *.JPG *.png *.PNG)")
        if len(filenames) > 0:
            self.ui.xray_textfield_all.setText(str(len(filenames)) + " Dateien ausgewählt")
            self.xray_filenames = filenames
            self.__check_button_activate()
            self.default_path = os.path.dirname(filenames[0])


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
    
    def __endoflip_button_clicked(self):
        """
        endoflip button callback
        """
        filename, _ = QFileDialog.getOpenFileName(self, 'Datei auswählen', self.default_path, "Excel (*.xlsx *.XLSX)")
        if len(filename) > 0:
            error = False
            try:
                self.endoflip_screenshot = process_endoflip_xlsx(filename)
            except:
                error = True
            if error or len(self.endoflip_screenshot['30']['aggregates']) != 4 or len(self.endoflip_screenshot['40']['aggregates']) != 4:
                self.ui.endoflip_textfield.setText("")
                QMessageBox.critical(self, "Ungültige Datei", "Fehler: Die Datei hat nicht das erwartete Format")
            else:
                self.ui.endoflip_textfield.setText(filename)
        self.__check_button_activate()
        self.default_path = os.path.dirname(filename)

    def __import_button_clicked(self):
        """
        import button callback
        """
        filenames, _ = QFileDialog.getOpenFileNames(self, 'Dateien auswählen', self.default_path,
                                                  "exportierte Dateien (*.achalasie)")
        if len(filenames) > 0:
            self.ui.import_textfield.setText(str(len(filenames)) + " Dateien ausgewählt")
            self.import_filenames = filenames
            self.__check_button_activate()

    def __check_button_activate(self):
        """
        activates visualization button if necessary files are selected
        """
        if (len(self.ui.csv_textfield.text()) > 0 and len(self.ui.xray_textfield_all.text()) > 0 or
                len(self.ui.import_textfield.text()) > 0):
            self.ui.visualization_button.setDisabled(False)
        else:
            self.ui.visualization_button.setDisabled(True)