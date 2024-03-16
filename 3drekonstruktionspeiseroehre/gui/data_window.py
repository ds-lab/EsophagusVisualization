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
from logic.database.pyqt_models import CustomPatientModel, CustomPreviousTherapyModel, CustomVisitsModel


class DataWindow(QMainWindow):

    def __init__(self, master_window: MasterWindow, patient_data: PatientData = PatientData()):
        super(DataWindow, self).__init__()
        self.selected_patient = None
        self.selected_visit = None
        self.selected_previous_therapy = None

        self.patient_model = None
        self.previous_therapies_model = None
        self.visit_model = None

        self.patient_array = None
        self.previous_therapies_array = None
        self.visits_array = None

        self.ui = uic.loadUi("./ui-files/show_data_window_design_neu.ui", self)

        self.patient_tableView = self.ui.patient_tableView
        self.therapy_tableView = self.ui.therapy_tableView
        self.visits_tableView = self.ui.visits_tableView

        self.master_window = master_window
        self.db = database.get_db()
        self.previous_therapy_service = PreviousTherapyService(self.db)
        self.patient_service = PatientService(self.db)
        self.visit_service = VisitService(self.db)

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
        self.ui.previous_therapy_add_button.clicked.connect(self.__previous_therapy_add_button_clicked)
        self.ui.previous_therapy_delete_button.clicked.connect(self.__previous_therapy_delete_button_clicked)
        self.ui.visit_add_button.clicked.connect(self.__visit_add_button_clicked)
        self.ui.visit_delete_button.clicked.connect(self.__visit_delete_button_clicked)
        self.ui.visit_update_button.clicked.connect(self.__visit_update_button_clicked)

        menu_button = QAction("Info", self)
        menu_button.triggered.connect(self.__menu_button_clicked)
        self.ui.menubar.addAction(menu_button)

        self.init_ui()

    # Function of the UI

    def __menu_button_clicked(self):
        """
        Info button callback. Shows information about file selection.
        """
        info_window = InfoWindow()
        info_window.show_file_selection_info()
        info_window.show()

    def init_ui(self):
        self.patients = self.patient_service.get_all_patients()
        self.patient_model = CustomPatientModel(self.patients)
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
        if self.patients is not None:
            self.patient_suggestions = [entry['patient_id'] for entry in self.patients]
        else:
            self.patient_suggestions = []

        # Set up QCompleter with autocomplete suggestions
        completer = QCompleter(self.patient_suggestions, self)
        # Case-insensitive autocomplete
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.ui.patient_id_field.setCompleter(completer)

        self.ui.patient_id_field.editingFinished.connect(
            self.__patient_id_filled)

    # Patient Functions

    def __context_menu_patient(self):
        menu = QtWidgets.QMenu()
        if self.patient_tableView.selectedIndexes():
            remove_data = menu.addAction("Remove Data")
            remove_data.setIcon(QtGui.QIcon("./media/remove.png"))
            remove_data.triggered.connect(lambda: self.patient_model.removeRows(self.patient_tableView.currentIndex()))
        cursor = QtGui.QCursor()
        menu.exec(cursor.pos())

    def __patient_add_button_clicked(self):
        if self.__validate_patient():
            if self.__patient_exists():
                if self.__to_update_patient():
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
            # Show the data of the selected patient in QTextEdit
            # pat_dict is needed again in case the patient was only updated
            pat_dict = {
                'patient_id': self.ui.patient_id_field.text(),
                'gender': self.ui.gender_dropdown.currentText(),
                'ethnicity': self.ui.ethnicity_dropdown.currentText(),
                'birth_year': self.ui.birthyear_calendar.date().toPyDate().year,
                'year_first_diagnosis': self.ui.firstdiagnosis_calendar.date().toPyDate().year,
                'year_first_symptoms': self.ui.firstsymptoms_calendar.date().toPyDate().year}
            output = ""
            for key, value in pat_dict.items():
                output += f"{key}: {value}\n"
            self.ui.selected_patient_text_patientview.setText(output)
            self.ui.selected_patient_text_visitview.setText(output)
            self.ui.selected_patient_text_visitdataview.setText(output)
            # Set the text of the select visit to "" until a visit for the patient is selected
            self.ui.selected_visit_text_visitview.setText("")
            self.ui.selected_visit_text_visitdataview.setText("")
            # Set the text of the select previous therapy to "" until a previous therapy is selected
            self.ui.selected_therapy_text_patientview.setText("")
        else:
            QMessageBox.warning(self, "Insufficient Data",
                                "Please fill out all patient data and make sure they are valid.")

    def __patient_update_button_clicked(self):
        if self.__validate_patient(): # check if patient data are valid
            if not self.__patient_exists(): # check if patient exists in database, execute if this is not the case
                if self.__to_create_patient(): # ask user if patient should be created
                    pat_dict = {'patient_id': self.ui.patient_id_field.text(),
                                'gender': self.ui.gender_dropdown.currentText(),
                                'ethnicity': self.ui.ethnicity_dropdown.currentText(),
                                'birth_year': self.ui.birthyear_calendar.date().toPyDate().year,
                                'year_first_diagnosis': self.ui.firstdiagnosis_calendar.date().toPyDate().year,
                                'year_first_symptoms': self.ui.firstsymptoms_calendar.date().toPyDate().year}
                    self.patient_service.create_patient(pat_dict)
            else: # if patient exists in database, patient data can be updated
                pat_dict = {
                    'gender': self.ui.gender_dropdown.currentText(),
                    'ethnicity': self.ui.ethnicity_dropdown.currentText(),
                    'birth_year': self.ui.birthyear_calendar.date().toPyDate().year,
                    'year_first_diagnosis': self.ui.firstdiagnosis_calendar.date().toPyDate().year,
                    'year_first_symptoms': self.ui.firstsymptoms_calendar.date().toPyDate().year}
                self.patient_service.update_patient(
                    self.ui.patient_id_field.text(), pat_dict)
            self.init_ui()
            # Show the data of the selected patient in QTextEdit
            # pat_dict is needed again in case the patient was only updated
            pat_dict = {
                'patient_id': self.ui.patient_id_field.text(),
                'gender': self.ui.gender_dropdown.currentText(),
                'ethnicity': self.ui.ethnicity_dropdown.currentText(),
                'birth_year': self.ui.birthyear_calendar.date().toPyDate().year,
                'year_first_diagnosis': self.ui.firstdiagnosis_calendar.date().toPyDate().year,
                'year_first_symptoms': self.ui.firstsymptoms_calendar.date().toPyDate().year}
            output = ""
            for key, value in pat_dict.items():
                output += f"{key}: {value}\n"
            self.ui.selected_patient_text_patientview.setText(output)
            self.ui.selected_patient_text_visitview.setText(output)
            self.ui.selected_patient_text_visitdataview.setText(output)
            # Set the text of the select visit to "" until a visit for the patient is selected
            self.ui.selected_visit_text_visitview.setText("")
            self.ui.selected_visit_text_visitdataview.setText("")
            # Set the text of the select previous therapy to "" until a previous therapy is selected
            self.ui.selected_therapy_text_patientview.setText("")
        else:
            QMessageBox.warning(self, "Insufficient Data", "Please fill out all patient data and make sure they are "
                                                           "valid.")

    def __patient_delete_button_clicked(self):
        self.patient_service.delete_patient(self.ui.patient_id_field.text()) # ToDo vorher checken ob der Patient existiert
        self.init_ui()
        self.selected_patient = None
        self.ui.selected_patient_text_patientview.setText("")
        self.ui.selected_patient_text_visitview.setText("")
        self.ui.selected_patient_text_visitdataview.setText("")
        # Set the text of the selected visit to ""
        self.ui.selected_visit_text_visitview.setText("")
        self.ui.selected_visit_text_visitdataview.setText("")
        # Set the text of the select previous therapy to ""
        self.ui.selected_therapy_text_patientview.setText("")

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
            self.ui.selected_patient_text_patientview.setText(output)
            self.ui.selected_patient_text_visitview.setText(output)
            self.ui.selected_patient_text_visitdataview.setText(output)
            # Set the text of the select visit to "" until a visit for the patient is selected
            self.ui.selected_visit_text_visitview.setText("")
            self.ui.selected_visit_text_visitdataview.setText("")
            # Set the text of the select previous therapy to "" until a previous therapy is selected
            self.ui.selected_therapy_text_patientview.setText("")

            self.selected_patient = str(self.patient_tableView.model().index(selected_row, 0).data())
            print(self.selected_patient)

            # Show the data of the selected patient in the drop-down/selection menu
            self.ui.patient_id_field.setText(
                str(self.patient_tableView.model().index(selected_row, 0).data()))
            self.__patient_id_filled()

            # Show all therapies of the selected patient
            # self.therapy_array = self.previous_therapy_service.get_prev_therapies_for_patient(
            #    self.ui.patient_id_field.text())

            self.__init_previous_therapies()
            self.__init_visits_of_patient()

    def __validate_patient(self):
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

    def __patient_exists(self):
        patient = self.patient_service.get_patient(
            self.ui.patient_id_field.text())
        if patient:
            return True
        return False

    def __to_update_patient(self):
        reply = QMessageBox.question(self, 'This Patient already exists in the database.',
                                     "Should the Patients data be updated?", QMessageBox.StandardButton.Yes |
                                     QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            return True
        return False

    def __to_create_patient(self):
        reply = QMessageBox.question(self, 'This Patient not yet exists in the database.',
                                     "Should the patient be created?", QMessageBox.StandardButton.Yes |
                                     QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            return True
        return False

    # Previous Therapy Functions

    def __init_previous_therapies(self):
        self.previous_therapies_array = self.previous_therapy_service.get_prev_therapies_for_patient(
            self.selected_patient)
        self.previous_therapies_model = CustomPreviousTherapyModel(self.previous_therapies_array)
        self.therapy_tableView.setModel(self.previous_therapies_model)
        self.therapy_tableView.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.therapy_tableView.customContextMenuRequested.connect(self.__context_menu_previous_therapies)
        self.therapy_tableView.verticalHeader().setDefaultSectionSize(30)
        self.therapy_tableView.setColumnWidth(0, 50)
        self.therapy_tableView.resizeColumnsToContents()
        self.therapy_tableView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.therapy_tableView.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.therapy_tableView.clicked.connect(self.__show_selected_previous_therapy_data)

    def __context_menu_previous_therapies(self):
        menu = QtWidgets.QMenu()
        if self.patient_tableView.selectedIndexes():
            remove_data = menu.addAction("Remove Data")
            remove_data.setIcon(QtGui.QIcon("./media/remove.png"))
            remove_data.triggered.connect(
                lambda: self.previous_therapies_model.removeRows(self.therapy_tableView.currentIndex()))
        cursor = QtGui.QCursor()
        menu.exec(cursor.pos())

    def __show_selected_previous_therapy_data(self):
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
            self.ui.selected_therapy_text_patientview.setText(output)

    def __previous_therapy_add_button_clicked(self):
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
                self.__init_previous_therapies()
            else:
                therapy_dict = {
                    'patient_id': self.selected_patient,
                    'therapy': self.ui.therapy_dropdown.currentText(),
                    'year': self.ui.therapy_calendar.date().toPyDate().year}
                self.previous_therapies_service.create_previous_therapy(therapy_dict)
                self.__init_previous_therapies()
        else:
            QMessageBox.warning(self, "Insufficient Data", "Please fill out all therapy data and make sure they are "
                                                           "valid.")

    def __previous_therapy_delete_button_clicked(self):
        self.previous_therapies_service.delete_previous_therapy(self.selected_previous_therapy)
        self.__init_previous_therapies()
        self.selected_previous_therapy = None
        self.ui.selected_therapy_text_patientview.setText("")

    # Visit Functions
    def __init_visits_of_patient(self):
        self.visits_array = self.visit_service.get_visits_for_patient(self.selected_patient)
        self.visits_model = CustomVisitsModel(self.visits_array)
        self.visits_tableView.setModel(self.visits_model)
        self.visits_tableView.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.visits_tableView.customContextMenuRequested.connect(self.__context_menu_visit)
        self.visits_tableView.verticalHeader().setDefaultSectionSize(30)
        self.visits_tableView.setColumnWidth(0, 50)
        self.visits_tableView.resizeColumnsToContents()
        self.visits_tableView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.visits_tableView.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.visits_tableView.clicked.connect(self.__show_selected_visit_data)

    def __context_menu_visit(self):
        menu = QtWidgets.QMenu()
        if self.visits_tableView.selectedIndexes():
            remove_data = menu.addAction("Remove Data")
            remove_data.setIcon(QtGui.QIcon("./media/remove.png"))
            remove_data.triggered.connect(lambda: self.visit_model.removeRows(self.visit_tableView.currentIndex()))
        cursor = QtGui.QCursor()
        menu.exec(cursor.pos())

    def __visit_add_button_clicked(self):
        visit_dict = {'patient_id': self.selected_patient,
                      'year_of_visit': self.ui.year_of_visit_calendar.date().toPyDate().year,
                      'visit_type': self.ui.visit_type_dropdown.currentText(),
                      'therapy_type': self.ui.therapy_type_dropdown.currentText(),
                      'months_after_therapy': self.ui.month_after_therapy_spin.value()}
        if self.__validate_visit():
            if self.__visit_exists():
                if self.__to_update_visit():
                    self.visit_service.update_visit(
                        self.selected_visit, visit_dict)
            else:
                self.visit_service.create_visit(visit_dict)
            self.__init_visits_of_patient()
            output = ""
            for key, value in visit_dict.items():
                output += f"{key}: {value}\n"
            self.ui.selected_visit_text_visitview.setText(output)
            self.ui.selected_visit_text_visitdataview.setText(output)
        else:
            QMessageBox.warning(self, "Insufficient Data",
                                "Please fill out all visit data and make sure they are valid.")

    def __visit_update_button_clicked(self):
        visit_dict = {'patient_id': self.selected_patient,
                      'year_of_visit': self.ui.year_of_visit_calendar.date().toPyDate().year,
                      'visit_type': self.ui.visit_type_dropdown.currentText(),
                      'therapy_type': self.ui.therapy_type_dropdown.currentText(),
                      'months_after_therapy': self.ui.month_after_therapy_spin.value()}
        if self.__validate_visit():
            if not self.__visit_exists():
                if self.__to_create_visit():
                    self.visit_service.create_visit(visit_dict)
            else:
                self.visit_service.update_visit(
                    self.selected_visit, visit_dict)
            self.__init_visits_of_patient()
            output = ""
            for key, value in visit_dict.items():
                output += f"{key}: {value}\n"
            self.ui.selected_visit_text_visitview.setText(output)
            self.ui.selected_visit_text_visitdataview.setText(output)
        else:
            QMessageBox.warning(self, "Insufficient Data", "Please fill out all visit data and make sure they are "
                                                           "valid.")

    def __visit_delete_button_clicked(self):
        if self.visit_exists():
            self.visit_service.delete_visit(
                self.selected_visit)
            self.__init_visits_of_patient()
            self.selected_visit = None
            self.ui.selected_visit_text.setText("")
        else:
            QMessageBox.warning(self, "Select Visit to Delete", "Please select a visit you wish to delete.")

    def __show_selected_visit_data(self):
        selected_indexes = self.visits_tableView.selectedIndexes()  # Get the indexes of all selected cells
        if selected_indexes:
            # Get the row number of the first selected index
            selected_row = selected_indexes[0].row()

            # Access data for all columns in the selected row
            data = []
            for column in range(self.visits_tableView.model().columnCount()):
                index = self.visits_tableView.model().index(selected_row, column)
                data.append(str(index.data()))

            labels = self.visits_model.columns

            # Show the data of the selected patient in QTextEdit
            output = ""
            for key, value in zip(labels, data):
                output += f"{key}: {value}\n"
            self.ui.selected_visit_text_visitview.setText(output)
            self.ui.selected_visit_text_visitdataview.setText(output)

            self.selected_visit = str(self.visits_tableView.model().index(selected_row, 0).data())

            # Show the data of the selected visit in the drop-down/selection menu
            visit = self.visit_service.get_visit(
                self.selected_visit)
            if visit:
                self.ui.year_of_visit_calendar.setDate(QDate(visit.year_of_visit, 1, 1))
                if visit.visit_type == "Initial Diagnostic":
                    self.ui.visit_type_dropdown.setCurrentIndex(1)
                elif visit.visit_type == "Therapy":
                    self.ui.visit_type_dropdown.setCurrentIndex(2)
                elif visit.visit_type == "Follow-Up Diagnostic":
                    self.ui.visit_type_dropdown.setCurrentIndex(3)
                if visit.therapy_type == "Botox":
                    self.ui.therapy_type_dropdown.setCurrentIndex(1)
                elif visit.therapy_type == "Pneumatic Dilitation":
                    self.ui.therapy_type_dropdown.setCurrentIndex(2)
                elif visit.therapy_type == "POEM":
                    self.ui.therapy_type_dropdown.setCurrentIndex(3)
                elif visit.therapy_type == "LHM":
                    self.ui.therapy_type_dropdown.setCurrentIndex(4)

    def __validate_visit(self):
        if (
                1900 < self.ui.year_of_visit_calendar.date().toPyDate().year <= datetime.now().year
                and self.ui.visit_type_dropdown.currentText() != "---"
                and self.ui.therapy_type_dropdown.currentText() != "---"
                and self.ui.month_after_therapy_spin.value() != -1
        ):
            return True
        return False

    def __visit_exists(self):
        if self.selected_visit:
            visit = self.visit_service.get_visit(
                self.selected_visit)
            if visit:
                return True
        return False

    def __to_update_visit(self):
        reply = QMessageBox.question(self, 'This Visit already exists in the database.',
                                     "Should the Visit data be updated?", QMessageBox.StandardButton.Yes |
                                     QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            return True
        return False

    def __to_create_visit(self):
        reply = QMessageBox.question(self, 'This Visit not yet exists in the database.',
                                     "Should the Visit be created?", QMessageBox.StandardButton.Yes |
                                     QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            return True
        return False
