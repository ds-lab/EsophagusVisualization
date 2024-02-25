import os
import pickle
import re
from pathlib import Path

import numpy as np
import pandas as pd
# from PyQt5.QtWidgets import QLineEdit
# from PyQt5 import uic
# from PyQt5.QtWidgets import QAction, QFileDialog, QMainWindow, QMessageBox
from PyQt6 import uic, QtCore
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QFileDialog, QMainWindow, QMessageBox, QVBoxLayout, QCompleter
from sqlalchemy.orm import sessionmaker

import config
import gui.visualization_window
from gui.info_window import InfoWindow
from gui.master_window import MasterWindow
from gui.xray_window_managment import ManageXrayWindows
from gui.previous_therapies_window import PreviousTherapiesWindow
from gui.show_data_window import ShowDataWindow
from logic.database import database
from logic.database.data_declarative_models import Patient, Visit
from logic.endoflip_data_processing import process_endoflip_xlsx
from logic.patient_data import PatientData
from logic.visit_data import VisitData
from logic.visualization_data import VisualizationData
from sqlalchemy import insert, select, and_, update
from logic.services.patient_service import PatientService
from logic.services.visit_service import VisitService


class FileSelectionWindow(QMainWindow):
    """Window where the user selects the needed files"""

    def __init__(self, master_window: MasterWindow, patient_data: PatientData = PatientData()):
        """
        init FileSelectionWindow
        :param master_window: the MasterWindow in which the next window will be displayed
        :param patient_data: an instance of PatientData
        """
        super().__init__()
        self.lineEdit = None
        self.ui = uic.loadUi("./ui-files/file_selection_window_design.ui", self)
        self.master_window: MasterWindow = master_window
        self.patient_data: PatientData = patient_data
        self.default_path = str(Path.home())
        self.import_filenames = []
        self.endoscopy_filenames = []
        self.xray_filenames = []
        self.endoscopy_image_positions = []
        self.endoflip_screenshot = None
        self.ui.visit_data_button.clicked.connect(self.__visit_data_button_clicked)
        self.ui.import_button.clicked.connect(self.__import_button_clicked)
        self.ui.visualization_button.clicked.connect(self.__visualization_button_clicked)
        self.ui.csv_button.clicked.connect(self.__csv_button_clicked)
        self.ui.xray_button_all.clicked.connect(self.__xray_button_clicked_all)
        self.ui.endoscopy_button.clicked.connect(self.__endoscopy_button_clicked)
        self.ui.endoflip_button.clicked.connect(self.__endoflip_button_clicked)
        self.ui.previous_therapies_check.stateChanged.connect(self.__previous_therapies_check_clicked)
        menu_button = QAction("Info", self)
        menu_button.triggered.connect(self.__menu_button_clicked)
        self.ui.menubar.addAction(menu_button)
        self.__check_button_activate()
        self.db = database.get_db()
        self.patient_service = PatientService(self.db)
        self.visit_service = VisitService(self.db)
        self.init_ui()


    def init_ui(self):
        Session = sessionmaker(bind=database.engine_local.connect())
        session = Session()

        rows = []
        for patient in session.query(Patient).all():
            rows.append((patient.patient_id, patient.ancestry, patient.birth_year, patient.previous_therapies))

        print(rows)

        patient_view = ShowDataWindow(self.master_window)
        patient_view.show()

        # Fetch all patient_id values
        patient_ids = session.query(Patient.patient_id).all()

        for patient_id in patient_ids:
            print(patient_id[0])
        suggestions = [patient_id[0] for patient_id in patient_ids]

        # Set up QCompleter with autocomplete suggestions
        completer = QCompleter(suggestions, self)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)  # Case-insensitive autocomplete
        self.ui.patient_id_field.setCompleter(completer)

        self.ui.patient_id_field.editingFinished.connect(self.__patient_id_filled)


    def __patient_id_filled(self):
        # ToDo: Felder mit echten Daten aus der DB für den jeweiligen Patienten füllen, wenn vorhanden
        d = QDate(2020, 6, 10)
        self.ui.birthdate_calendar.setDate(d)
        self.ui.gender_dropdown.setCurrentIndex(1)

    def __menu_button_clicked(self):
        """
        Info button callback. Shows information about file selection.
        """
        info_window = InfoWindow()
        info_window.show_file_selection_info()
        info_window.show()

    def __visit_data_button_clicked(self):
        """
        checks if all patient and visit data are filled out
        """
        measure = None
        if self.ui.diagnostics_radio.isChecked() == 1:
            measure = "diagnostics"
        elif self.ui.therapy_radio.isChecked() == 1:
            measure = "therapy"
        elif self.ui.follow_up_radio.isChecked() == 1:
            measure = "follow_up"

        age = self.ui.date_calendar.date().toPyDate().year - self.ui.birthdate_calendar.date().toPyDate().year - (
                (self.ui.date_calendar.date().toPyDate().month, self.ui.date_calendar.date().toPyDate().day) <
                (self.ui.birthdate_calendar.date().toPyDate().month, self.ui.birthdate_calendar.date().toPyDate().day))

        if (
                len(self.ui.patient_id_field.text()) > 0
                and self.ui.gender_dropdown.currentText() != "---"
                and self.ui.ancestry_dropdown.currentText() != "---"
                and
                (
                        self.ui.diagnostics_radio.isChecked() or self.ui.therapy_radio.isChecked() or self.ui.follow_up_radio.isChecked())
                and (not self.ui.therapy_radio.isChecked() or self.ui.method_dropdown.currentText() != "---")
                and (not self.ui.follow_up_radio.isChecked() or self.ui.months_after_therapy_spin.value() != -1)
                and len(self.ui.center_id_field.text()) > 0
        ):
            patient = self.patient_service.get_patient(self.ui.patient_id_field.text())
            if patient:
                reply = QMessageBox.question(self, 'This Patient already exists in the database.',
                                             "Should the Patients data be updated?", QMessageBox.StandardButton.Yes |
                                             QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:
                    pat_dict = {'ancestry': self.ui.ancestry_dropdown.currentText(),
                                'birth_year': self.ui.birthdate_calendar.date().toPyDate().year,
                                'previous_therapies': self.ui.previous_therapies_check.isChecked()}
                    self.patient_service.update_patient(self.ui.patient_id_field.text(), pat_dict)
            else:
                pat_dict = {
                    'patient_id': self.ui.patient_id_field.text(),
                    'ancestry': self.ui.ancestry_dropdown.currentText(),
                    'birth_year': self.ui.birthdate_calendar.date().toPyDate().year,
                    'previous_therapies': self.ui.previous_therapies_check.isChecked()}
                self.patient_service.create_patient(pat_dict)
                visit_dict = {
                    "patient_id": self.ui.patient_id_field.text(),
                    "measure": measure,
                    "center": self.ui.center_id_field.text(),
                    "age_at_visit": age
                }
                self.visit_service.create_visit(visit_dict)
            # Session = sessionmaker(bind=database.engine_local.connect())
            # with Session() as session:
            #     db_patient = session.query(Patient).get(self.ui.patient_id_field.text())
            #     if db_patient:
            #         reply = QMessageBox.question(self, 'This Patient already exists in the database.',
            #                                      "Should the Patients data be updated?", QMessageBox.StandardButton.Yes |
            #                                      QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            #         if reply == QMessageBox.StandardButton.Yes:
            #             pat_dict = {'ancestry': self.ui.ancestry_dropdown.currentText(),
            #                         'birth_year': self.ui.birthdate_calendar.date().toPyDate().year,
            #                         'previous_therapies': self.ui.previous_therapies_check.isChecked()}
            #             update_query = update(Patient).where(Patient.patient_id == self.ui.patient_id_field.text()).values(pat_dict)
            #             session.execute(update_query)
            #     else:
            #         patient = Patient(
            #             patient_id=self.ui.patient_id_field.text(),
            #             ancestry=self.ui.ancestry_dropdown.currentText(),
            #             birth_year=self.ui.birthdate_calendar.date().toPyDate().year,
            #             previous_therapies=self.ui.previous_therapies_check.isChecked()
            #         )
            #         visit = Visit(
            #             # ToDo: wie soll die VisitID festgelegt werden? Wenn man einen Visit später anpassen will muss man eigentlich die Visit-ID kennen.
            #             patient_id=self.ui.patient_id_field.text(),
            #             measure=measure,
            #             center=self.ui.center_id_field.text(),
            #             age_at_visit=age)
            #
            #         session.add(patient)
            #         session.add(visit)
            #     session.commit()
        else:
            QMessageBox.warning(self, "Insufficient Data", "Please fill out all patient and visit data.")

        # list_patients = list_data_windows.ListPatients()
        # list_patients.show()

    def __previous_therapies_check_clicked(self):
        """
        checks if the previous therapies field is checked
        shows previous therapies window if previous therapies field is checked
        """
        if self.ui.previous_therapies_check.isChecked():
            print("Checkbox checked")
            previous_therapies = PreviousTherapiesWindow(self.master_window)
            previous_therapies.show()
            Session = sessionmaker(bind=database.engine_local.connect())
            session = Session()

            rows = []
            for patient in session.query(Patient).all():
                rows.append((patient.patient_id, patient.ancestry, patient.birth_year, patient.previous_therapies))

            print(rows)

            patient_view = ShowDataWindow(self.master_window, rows)
            patient_view.show()
        else:
            print("Checkbox not checked")

    def __visualization_button_clicked(self):
        """
        Visualization button callback. Initiates the visualization process.
        """
        if len(self.ui.csv_textfield.text()) > 0 and len(self.ui.xray_textfield_all.text()) > 0:
            if len(self.ui.visualization_namefield.text()) > 0:
                # Add name if user chooses to name the reconstruction
                name = self.ui.visualization_namefield.text()
                if self.ui.visualization_namefield.text() in self.patient_data.visit_data_dict.keys():
                    QMessageBox.critical(self, "Rekonstruktionsname nicht eindeutig",
                                         "Fehler: Rekonstruktionsnamen müssen eindeutig sein.")
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
                # Check if a '.achalasie'-file is loaded.
                # This check is probably not really necessary, because it should only be possible to select '.achalasie' files.
                file_ending = import_filename.split("/")[-1].split(".")[-1]
                if file_ending != "achalasie":
                    QMessageBox.information(self, "Falsche Dateiendung",
                                            "Die Dateiendung muss '.achalasie' sein.\n"
                                            f"Die Datei {import_filename} kann nicht geladen werden.")
                else:
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
        CSV button callback. Handles CSV file selection.
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
        X-ray button callback. Handles X-ray file selection for all files.
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
        Endoscopy button callback. Handles endoscopy image selection.
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
        EndoFLIP button callback. Handles EndoFLIP .xlsx file selection.
        """
        filename, _ = QFileDialog.getOpenFileName(self, 'Datei auswählen', self.default_path, "Excel (*.xlsx *.XLSX)")
        if len(filename) > 0:
            error = False
            try:
                self.endoflip_screenshot = process_endoflip_xlsx(filename)
            except:
                error = True
            if error or len(self.endoflip_screenshot['30']['aggregates']) != 4 or len(
                    self.endoflip_screenshot['40']['aggregates']) != 4:
                self.ui.endoflip_textfield.setText("")
                QMessageBox.critical(self, "Ungültige Datei", "Fehler: Die Datei hat nicht das erwartete Format")
            else:
                self.ui.endoflip_textfield.setText(filename)
        self.__check_button_activate()
        self.default_path = os.path.dirname(filename)

    def __import_button_clicked(self):
        """
        Import button callback. Handles import file selection.
        """
        # Inform the user, that only '.achalasie'-files from trustworthy sources should be loaded
        QMessageBox.warning(self, "Achtung!",
                            "Laden Sie nur '.achalasie'-Dateien,\n"
                            "welche Sie selbst mit diesem Programm\n"
                            "exportiert haben!")

        filenames, _ = QFileDialog.getOpenFileNames(self, 'Dateien auswählen', self.default_path,
                                                    "exportierte Dateien (*.achalasie)")
        if len(filenames) > 0:
            self.ui.import_textfield.setText(str(len(filenames)) + " Dateien ausgewählt")
            self.import_filenames = filenames
            self.__check_button_activate()

    def __check_button_activate(self):
        """
        activates the visualization button if necessary files are selected
        """
        if (len(self.ui.csv_textfield.text()) > 0 and len(self.ui.xray_textfield_all.text()) > 0 or
                len(self.ui.import_textfield.text()) > 0):
            self.ui.visualization_button.setDisabled(False)
        else:
            self.ui.visualization_button.setDisabled(True)
