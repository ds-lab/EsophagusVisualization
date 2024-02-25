import os
import pickle
import re
from pathlib import Path
from datetime import datetime

from PyQt6 import QtCore, uic, QtWidgets, QtGui
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QWidget, QTableWidget, QTableWidgetItem, QHBoxLayout, QMainWindow, QMessageBox
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QFileDialog, QMainWindow, QMessageBox, QVBoxLayout, QCompleter

from sqlalchemy.orm import sessionmaker
from logic.patient_data import PatientData
from logic.visit_data import VisitData
from gui.master_window import MasterWindow
import gui.visualization_window
from gui.info_window import InfoWindow
from gui.master_window import MasterWindow
from gui.xray_window_managment import ManageXrayWindows
from gui.previous_therapies_window import PreviousTherapiesWindow
from logic.database import database
from logic.database.data_declarative_models import Patient
from logic.services.patient_service import PatientService
from logic.services.visit_service import VisitService

from logic.database.pyqt_models import CustomPatientModel


class DataWindow(QMainWindow):

    def __init__(self, master_window: MasterWindow, patient_data: PatientData = PatientData()):
        super(DataWindow, self).__init__()
        self.model = None
        self.user_data = None
        self.ui = uic.loadUi("./ui-files/show_data_window_design.ui", self)
        self.tableView = self.ui.tableView
        self.master_window = master_window
        self.db = database.get_db()
        self.patient_service = PatientService(self.db)
        self.visit_service = VisitService(self.db)

        # Data from DB have to be loaded into the correct data-structure for processing
        self.patient_data: PatientData = patient_data
        self.default_path = str(Path.home())
        self.import_filenames = []
        self.endoscopy_filenames = []
        self.xray_filenames = []
        self.endoscopy_image_positions = []
        self.endoflip_screenshot = None

        # Connect Buttons to Functions
        self.ui.patient_add_button.clicked.connect(self.__patient_add_button_clicked)

        menu_button = QAction("Info", self)
        menu_button.triggered.connect(self.__menu_button_clicked)
        self.ui.menubar.addAction(menu_button)

        self.init_ui()

    def init_ui(self):
        Session = sessionmaker(bind=database.engine_local.connect())
        session = Session()

        patientsArr = []
        for patient in session.query(Patient).all():
            patientsArr.append(patient.toDict())

        self.user_data = patientsArr

        # self.user_data = self.patient_service.get_all_patients()
        print(f"USER DATA: {self.user_data}")
        # self.user_data = databaseOperations.get_multiple_data()
        self.model = CustomPatientModel(self.user_data)
        # self.delegate = InLineEditDelegate() # for inline editing
        self.tableView.setModel(self.model)
        # self.tableView.setItemDelegate(self.delegate)
        self.tableView.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.tableView.customContextMenuRequested.connect(self.context_menu)
        self.tableView.verticalHeader().setDefaultSectionSize(30)
        self.tableView.setColumnWidth(0, 50)
        self.tableView.resizeColumnsToContents()
        # self.tableView.hideColumn(0)

        # Collect all patient_ids in a list to make auto-complete suggestions
        self.patient_suggestions = [entry['patient_id'] for entry in self.user_data]

        # Set up QCompleter with autocomplete suggestions
        completer = QCompleter(self.patient_suggestions, self)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)  # Case-insensitive autocomplete
        self.ui.patient_id_field.setCompleter(completer)

        self.ui.patient_id_field.editingFinished.connect(self.__patient_id_filled)

    def context_menu(self):
        menu = QtWidgets.QMenu()
        add_data = menu.addAction("Add New Data")
        add_data.setIcon(QtGui.QIcon("./media/add-icon.png"))
        add_data.triggered.connect(lambda: self.model.insertRows())
        if self.tableView.selectedIndexes():
            remove_data = menu.addAction("Remove Data")
            remove_data.setIcon(QtGui.QIcon("./media/remove.png"))
            remove_data.triggered.connect(lambda: self.model.removeRows(self.tableView.currentIndex()))
        cursor = QtGui.QCursor()
        menu.exec(cursor.pos())

    def __menu_button_clicked(self):
        """
        Info button callback. Shows information about file selection.
        """
        info_window = InfoWindow()
        info_window.show_file_selection_info()
        info_window.show()

    def __patient_add_button_clicked(self):
        """
        checks if all patient data are filled out
        """

        if (
                len(self.ui.patient_id_field.text()) > 0
                and self.ui.gender_dropdown.currentText() != "---"
                and self.ui.ethnicity_dropdown.currentText() != "---"
                and 1900 < self.ui.birthyear_calendar.date().toPyDate().year <= datetime.now().year
                and 1900 < self.ui.firstdiagnosis_calendar.date().toPyDate().year <= datetime.now().year
                and 1990 < self.ui.firstsymptoms_calendar.date().toPyDate().year <= datetime.now().year
        ):
            patient = self.patient_service.get_patient(self.ui.patient_id_field.text())
            if patient:
                reply = QMessageBox.question(self, 'This Patient already exists in the database.',
                                             "Should the Patients data be updated?", QMessageBox.StandardButton.Yes |
                                             QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:
                    pat_dict = {'gender': self.ui.gender_dropdown.currentText(),
                                'ethnicity': self.ui.ethnicity_dropdown.currentText(),
                                'birth_year': self.ui.birthyear_calendar.date().toPyDate().year,
                                'year_first_diagnosis': self.ui.firstdiagnosis_calendar.date().toPyDate().year,
                                'year_first_symptoms': self.ui.firstsymptoms_calendar.date().toPyDate().year}
                    self.patient_service.update_patient(self.ui.patient_id_field.text(), pat_dict)
            else:
                pat_dict = {
                    'patient_id': self.ui.patient_id_field.text(),
                    'gender': self.ui.gender_dropdown.currentText(),
                    'ethnicity': self.ui.ethnicity_dropdown.currentText(),
                    'birth_year': self.ui.birthyear_calendar.date().toPyDate().year,
                    'year_first_diagnosis': self.ui.firstdiagnosis_calendar.date().toPyDate().year,
                    'year_first_symptoms': self.ui.firstsymptoms_calendar.date().toPyDate().year}
                self.patient_service.create_patient(pat_dict)
            self.init_ui()
        else:
            QMessageBox.warning(self, "Insufficient Data", "Please fill out all patient data and make sure they are valid.")

    def __patient_id_filled(self):
        # ToDo: Felder mit echten Daten aus der DB für den jeweiligen Patienten füllen, wenn vorhanden
        d = QDate(2020, 6, 10)
        self.ui.birthdate_calendar.setDate(d)
        self.ui.gender_dropdown.setCurrentIndex(1)





