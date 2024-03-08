from pathlib import Path
from datetime import datetime
from PyQt6 import QtCore, uic, QtWidgets, QtGui
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMainWindow, QMessageBox
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMainWindow, QMessageBox, QCompleter
from sqlalchemy.orm import sessionmaker
from logic.patient_data import PatientData
from gui.master_window import MasterWindow
from gui.info_window import InfoWindow
from gui.master_window import MasterWindow
from logic.database import database
from logic.database.data_declarative_models import Patient
from logic.database.data_declarative_models import PreviousTherapy
from logic.services.patient_service import PatientService
from logic.services.visit_service import VisitService
from logic.services.previous_therapy_service import PreviousTherapyService
from logic.database.pyqt_models import CustomPatientModel
from logic.database.pyqt_models import CustomPreviousTherapyModel


class DataWindow(QMainWindow):

    def __init__(self, master_window: MasterWindow, patient_data: PatientData = PatientData()):
        super(DataWindow, self).__init__()
        self.selected_patient = None
        self.patient_model = None
        self.patient_array = None
        self.previous_therapies_model = None
        self.previous_therapies_array = None
        self.selected_previous_therapy = None
        self.ui = uic.loadUi("./ui-files/show_data_window_design_neu.ui", self)
        self.patient_tableView = self.ui.patient_tableView
        self.therapy_tableView = self.ui.therapy_tableView
        self.master_window = master_window
        self.db = database.get_db()
        self.previous_therapies_service = PreviousTherapyService(self.db)
        self.patient_service = PatientService(self.db)
        self.visit_service = VisitService(self.db)
        self.previous_therapy_service = PreviousTherapyService(self.db)

        # ToDo Evtl. diese erst später initalisieren, wenn die Rekonstruktion erstellt werden soll
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
        self.ui.patient_update_button.clicked.connect(self.__patient_update_button_clicked)
        self.ui.patient_delete_button.clicked.connect(self.__patient_delete_button_clicked)
        self.ui.therapy_add_button.clicked.connect(self.__therapy_add_button_clicked)
        self.ui.therapy_delete_button.clicked.connect(self.__therapy_delete_button_clicked)

        menu_button = QAction("Info", self)
        menu_button.triggered.connect(self.__menu_button_clicked)
        self.ui.menubar.addAction(menu_button)

        self.init_ui()

    def __menu_button_clicked(self):
        """
        Info button callback. Shows information about file selection.
        """
        info_window = InfoWindow()
        info_window.show_file_selection_info()
        info_window.show()

    def init_ui(self):
        Session = sessionmaker(bind=database.engine_local.connect())
        session = Session()

        patientsArr = []
        for patient in session.query(Patient).all():
            patientsArr.append(patient.toDict())

        self.patient_array = patientsArr

        # self.user_data = self.patient_service.get_all_patients()
        print(f"USER DATA: {self.patient_array}")
        self.patient_model = CustomPatientModel(self.patient_array)
        self.patient_tableView.setModel(self.patient_model)
        self.patient_tableView.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.patient_tableView.customContextMenuRequested.connect(self.__context_menu_patient)
        self.patient_tableView.verticalHeader().setDefaultSectionSize(30)
        self.patient_tableView.setColumnWidth(0, 50)
        self.patient_tableView.resizeColumnsToContents()
        self.patient_tableView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.patient_tableView.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.patient_tableView.clicked.connect(self.__show_selected_patient_data)
        # self.tableView.hideColumn(0)

        # Collect all patient_ids in a list to make auto-complete suggestions
        self.patient_suggestions = [entry['patient_id']
                                    for entry in self.patient_array]

        # Set up QCompleter with autocomplete suggestions
        completer = QCompleter(self.patient_suggestions, self)
        # Case-insensitive autocomplete
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.ui.patient_id_field.setCompleter(completer)

        self.ui.patient_id_field.editingFinished.connect(
            self.__patient_id_filled)

    def __context_menu_patient(self):
        menu = QtWidgets.QMenu()
        if self.patient_tableView.selectedIndexes():
            remove_data = menu.addAction("Remove Data")
            remove_data.setIcon(QtGui.QIcon("./media/remove.png"))
            remove_data.triggered.connect(lambda: self.patient_model.removeRows(self.patient_tableView.currentIndex()))
        cursor = QtGui.QCursor()
        menu.exec(cursor.pos())

    def __patient_add_button_clicked(self):

        if self.validate_patient():

            pat_dict = None

            if self.patient_exists():
                if self.to_update_patient():
                    pat_dict = {'gender': self.ui.gender_dropdown.currentText(),
                                'ethnicity': self.ui.ethnicity_dropdown.currentText(),
                                'birth_year': self.ui.birthyear_calendar.date().toPyDate().year,
                                'year_first_diagnosis': self.ui.firstdiagnosis_calendar.date().toPyDate().year,
                                'year_first_symptoms': self.ui.firstsymptoms_calendar.date().toPyDate().year}
                    self.patient_service.update_patient(
                        self.ui.patient_id_field.text(), pat_dict)
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
            QMessageBox.warning(self, "Insufficient Data",
                                "Please fill out all patient data and make sure they are valid.")

    def __patient_update_button_clicked(self):

        if self.validate_patient():

            pat_dict = None

            if not self.patient_exists():
                if self.to_create_patient():
                    pat_dict = {'patient_id': self.ui.patient_id_field.text(),
                                'gender': self.ui.gender_dropdown.currentText(),
                                'ethnicity': self.ui.ethnicity_dropdown.currentText(),
                                'birth_year': self.ui.birthyear_calendar.date().toPyDate().year,
                                'year_first_diagnosis': self.ui.firstdiagnosis_calendar.date().toPyDate().year,
                                'year_first_symptoms': self.ui.firstsymptoms_calendar.date().toPyDate().year}
                    self.patient_service.create_patient(pat_dict)
            else:
                pat_dict = {
                    'gender': self.ui.gender_dropdown.currentText(),
                    'ethnicity': self.ui.ethnicity_dropdown.currentText(),
                    'birth_year': self.ui.birthyear_calendar.date().toPyDate().year,
                    'year_first_diagnosis': self.ui.firstdiagnosis_calendar.date().toPyDate().year,
                    'year_first_symptoms': self.ui.firstsymptoms_calendar.date().toPyDate().year}

                self.patient_service.update_patient(
                    self.ui.patient_id_field.text(), pat_dict)

            self.init_ui()
        else:
            QMessageBox.warning(self, "Insufficient Data", "Please fill out all patient data and make sure they are "
                                                           "valid.")

    def __patient_delete_button_clicked(self):
        self.patient_service.delete_patient(self.ui.patient_id_field.text())
        self.init_ui()
        self.selected_patient = None
        self.ui.selected_patient_text.setText("")

    def __patient_id_filled(self):
        patient = self.patient_service.get_patient(
            self.ui.patient_id_field.text())
        if patient:
            self.ui.birthyear_calendar.setDate(QDate(patient.birth_year, 1, 1))
            self.ui.firstdiagnosis_calendar.setDate(
                QDate(patient.year_first_diagnosis, 1, 1))
            self.ui.firstsymptoms_calendar.setDate(
                QDate(patient.year_first_symptoms, 1, 1))
            if patient.gender == "male":
                self.ui.gender_dropdown.setCurrentIndex(1)
            elif patient.gender == "female":
                self.ui.gender_dropdown.setCurrentIndex(2)
            else:
                self.ui.gender_dropdown.setCurrentIndex(3)
            if patient.ethnicity == "American Indian or Alaska Native":
                self.ui.ethnicity_dropdown.setCurrentIndex(1)
            elif patient.ethnicity == "Asian":
                self.ui.ethnicity_dropdown.setCurrentIndex(2)
            elif patient.ethnicity == "Black or African American":
                self.ui.ethnicity_dropdown.setCurrentIndex(3)
            elif patient.ethnicity == "Native Hawaiian or Other Pacific Islander":
                self.ui.ethnicity_dropdown.setCurrentIndex(4)
            elif patient.ethnicity == "White":
                self.ui.ethnicity_dropdown.setCurrentIndex(5)
            else:
                self.ui.ethnicity_dropdown.setCurrentIndex(6)

    def __show_selected_patient_data(self):
        selected_indexes = self.patient_tableView.selectedIndexes()  # Get the indexes of all selected cells
        if selected_indexes:
            # Get the row number of the first selected index
            selected_row = selected_indexes[0].row()

            # Access data for all columns in the selected row
            data = []
            for column in range(self.patient_tableView.model().columnCount()):
                index = self.patient_tableView.model().index(selected_row, column)
                data.append(str(index.data()))

            labels = self.patient_model.columns

            # Show the data of the selected patient in QTextEdit
            output = ""
            for key, value in zip(labels, data):
                output += f"{key}: {value}\n"
            self.ui.selected_patient_text.setText(output)

            self.selected_patient = str(self.patient_tableView.model().index(selected_row, 0).data())

            # Show the data of the selected patient in the drop-down/selection menu
            self.ui.patient_id_field.setText(
                str(self.patient_tableView.model().index(selected_row, 0).data()))
            self.__patient_id_filled()

            # Show all therapies of the selected patient
            #self.therapy_array = self.previous_therapy_service.get_prev_therapies_for_patient(
            #    self.ui.patient_id_field.text())

            self.init_previous_therapies()

    def validate_patient(self):
        if (
            len(self.ui.patient_id_field.text()) > 0
            and self.ui.gender_dropdown.currentText() != "---"
            and self.ui.ethnicity_dropdown.currentText() != "---"
            and 1900 < self.ui.birthyear_calendar.date().toPyDate().year <= datetime.now().year
            and 1900 < self.ui.firstdiagnosis_calendar.date().toPyDate().year <= datetime.now().year
            and 1900 < self.ui.firstsymptoms_calendar.date().toPyDate().year <= datetime.now().year
        ):
            return True
        return False

    def patient_exists(self):
        patient = self.patient_service.get_patient(
            self.ui.patient_id_field.text())
        if patient:
            return True
        return False

    def to_update_patient(self):
        reply = QMessageBox.question(self, 'This Patient already exists in the database.',
                                     "Should the Patients data be updated?", QMessageBox.StandardButton.Yes |
                                     QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            return True
        return False

    def to_create_patient(self):
        reply = QMessageBox.question(self, 'This Patient not yet exists in the database.',
                                     "Should the patient be created?", QMessageBox.StandardButton.Yes |
                                     QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            return True
        return False

    def init_previous_therapies(self):
        Session = sessionmaker(bind=database.engine_local.connect())
        session = Session()

        therapyArr = []
        for therapy in session.query(PreviousTherapy).filter(
                PreviousTherapy.patient_id == self.selected_patient).all():
            therapyArr.append(therapy.toDict())

        self.previous_therapies_array = therapyArr
        print(f"THERAPY DATA: {self.previous_therapies_array}")
        self.previous_therapies_model = CustomPreviousTherapyModel(self.previous_therapies_array)
        self.therapy_tableView.setModel(self.previous_therapies_model)
        self.therapy_tableView.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.therapy_tableView.customContextMenuRequested.connect(self.__context_menu_therapies)
        self.therapy_tableView.verticalHeader().setDefaultSectionSize(30)
        self.therapy_tableView.setColumnWidth(0, 50)
        self.therapy_tableView.resizeColumnsToContents()
        self.therapy_tableView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.therapy_tableView.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.therapy_tableView.clicked.connect(self.__show_selected_therapy_data)

    def __context_menu_therapies(self):
        menu = QtWidgets.QMenu()
        if self.patient_tableView.selectedIndexes():
            remove_data = menu.addAction("Remove Data")
            remove_data.setIcon(QtGui.QIcon("./media/remove.png"))
            remove_data.triggered.connect(
                lambda: self.previous_therapies_model.removeRows(self.therapy_tableView.currentIndex()))
        cursor = QtGui.QCursor()
        menu.exec(cursor.pos())

    def __show_selected_therapy_data(self):
        selected_indexes = self.therapy_tableView.selectedIndexes()  # Get the indexes of all selected cells
        if selected_indexes:
            selected_row = selected_indexes[0].row()  # Get the row number of the first selected index

            # Access data for all columns in the selected row
            data = []
            for column in range(self.therapy_tableView.model().columnCount()):
                index = self.therapy_tableView.model().index(selected_row, column)
                data.append(str(index.data()))

            labels = self.previous_therapies_model.columns

            self.selected_previous_therapy = str(self.therapy_tableView.model().index(selected_row, 0).data())

            # Show the data of the selected patient in QTextEdit
            output = ""
            for key, value in zip(labels, data):
                output += f"{key}: {value}\n"
            self.ui.selected_therapy_text.setText(output)

    def __therapy_add_button_clicked(self):
        if (
                self.ui.therapy_dropdown.currentText() != "---"
                and (1900 < self.ui.therapy_calendar.date().toPyDate().year <= datetime.now().year or
                     self.ui.therapy_year_unknown_checkbox.isChecked())
        ):
            if self.ui.therapy_year_unknown_checkbox.isChecked():
                therapy_dict = {
                    'patient_id': self.selected_patient,
                    'therapy': self.ui.therapy_dropdown.currentText(),
                    'year_not_known': True}
                self.previous_therapies_service.create_previous_therapy(therapy_dict)
                self.init_previous_therapies()
            else:
                therapy_dict = {
                    'patient_id': self.selected_patient,
                    'therapy': self.ui.therapy_dropdown.currentText(),
                    'year': self.ui.therapy_calendar.date().toPyDate().year}
                self.previous_therapies_service.create_previous_therapy(therapy_dict)
                self.init_previous_therapies()
        else:
            QMessageBox.warning(self, "Insufficient Data", "Please fill out all therapy data and make sure they are "
                                                           "valid.")

    def __therapy_delete_button_clicked(self):
        self.previous_therapies_service.delete_previous_therapy(self.selected_previous_therapy)
        self.init_previous_therapies()
        self.selected_previous_therapy = None
        self.ui.selected_therapy_text.setText("")
