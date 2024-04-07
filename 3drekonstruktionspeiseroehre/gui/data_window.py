import os
import re
from pathlib import Path
from datetime import datetime
import config

from PyQt6 import QtCore, uic, QtWidgets, QtGui
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMainWindow, QMessageBox, QFileDialog, QCompleter
from PyQt6.QtCore import Qt, QDate, QSortFilterProxyModel
from logic.patient_data import PatientData
from gui.master_window import MasterWindow
from gui.info_window import InfoWindow
from gui.set_textfields import setText
from logic.datainput.endoflip_data_processing import process_endoflip_xlsx, conduct_endoflip_file_upload
from logic.datainput.endoscopy_data_processing import process_and_upload_endoscopy_images
from logic.datainput.barium_swallow_data_processing import process_and_upload_barium_swallow_images
from logic.datainput.manometry_data_processing import process_and_upload_manometry_file
from logic.database import database
from logic.datainput.validate_input_data import DataValidation
from logic.datainput.check_data_existence import CheckDataExistence
from logic.datainput.popup_windows import PopupWindow
from logic.services.patient_service import PatientService
from logic.services.visit_service import VisitService
from logic.services.eckardtscore_service import EckardtscoreService
from logic.services.manometry_service import ManometryService, ManometryFileService
from logic.services.previous_therapy_service import PreviousTherapyService
from logic.services.endoscopy_service import EndoscopyFileService
from logic.services.endoflip_service import EndoflipFileService
from logic.services.barium_swallow_service import BariumSwallowFileService
from logic.services.botox_injection_service import BotoxInjectionService
from logic.database.pyqt_models import CustomPatientModel, CustomPreviousTherapyModel, CustomVisitsModel


class DataWindow(QMainWindow):

    def __init__(self, master_window: MasterWindow, patient_data: PatientData = PatientData()):
        super(DataWindow, self).__init__()
        self.selected_patient = None
        self.selected_visit = None
        self.selected_previous_therapy = None

        self.patient_model = None
        self.patient_proxyModel = None
        self.previous_therapies_model = None
        self.visit_model = None

        self.patient_array = None
        self.previous_therapies_array = None
        self.visits_array = None

        # For displaying images
        self.endoscopy_image_index = None

        self.ui = uic.loadUi("./ui-files/show_data_window_design_neu2.ui", self)

        self.patient_tableView = self.ui.patient_tableView
        self.therapy_tableView = self.ui.therapy_tableView
        self.visits_tableView = self.ui.visits_tableView

        self.master_window = master_window
        self.db = database.get_db()

        self.patient_service = PatientService(self.db)
        self.previous_therapy_service = PreviousTherapyService(self.db)
        self.visit_service = VisitService(self.db)
        self.eckardtscore_service = EckardtscoreService(self.db)
        self.manometry_service = ManometryService(self.db)
        self.manometry_file_service = ManometryFileService(self.db)
        self.barium_swallow_file_service = BariumSwallowFileService(self.db)
        self.endoscopy_file_service = EndoscopyFileService(self.db)
        self.endoflip_file_service = EndoflipFileService(self.db)
        self.botox_injection_service = BotoxInjectionService(self.db)

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
        # Patients Tab
        self.ui.patient_add_button.clicked.connect(self.__patient_add_button_clicked)
        self.ui.patient_update_button.clicked.connect(self.__patient_update_button_clicked)
        self.ui.patient_delete_button.clicked.connect(self.__patient_delete_button_clicked)
        self.ui.patient_reset_filter_button.clicked.connect(self.__patients_reset_filter_button_clicked)
        # Filter Patients
        self.ui.patient_id_radio.toggled.connect(self.__patients_apply_filter)
        self.ui.birthyear_radio.toggled.connect(self.__patients_apply_filter)
        self.ui.gender_radio.toggled.connect(self.__patients_apply_filter)
        self.ui.ethnicity_radio.toggled.connect(self.__patients_apply_filter)
        self.ui.firstdiagnosis_radio.toggled.connect(self.__patients_apply_filter)
        self.ui.firstsymptoms_radio.toggled.connect(self.__patients_apply_filter)
        self.ui.center_radio.toggled.connect(self.__patients_apply_filter)
        # Previous Therapies
        self.ui.previous_therapy_add_button.clicked.connect(self.__previous_therapy_add_button_clicked)
        self.ui.previous_therapy_delete_button.clicked.connect(self.__previous_therapy_delete_button_clicked)
        # Visits Tab
        self.ui.visit_add_button.clicked.connect(self.__visit_add_button_clicked)
        self.ui.visit_delete_button.clicked.connect(self.__visit_delete_button_clicked)
        # Eckardt Score
        self.ui.add_eckardt_score_button.clicked.connect(self.__add_eckardt_score_button_clicked)
        self.ui.delete_eckardt_score_button.clicked.connect(self.__delete_eckardt_score_button_clicked)
        # Visit Data Tab
        # Manometry
        self.ui.add_manometry_button.clicked.connect(self.__add_manometry)
        self.ui.delete_manometry_button.clicked.connect(self.__delete_manometry)
        self.ui.manometry_file_upload_button.clicked.connect(self.__upload_manometry_file)
        # Barium Swallow / TBE
        self.ui.tbe_file_upload_button.clicked.connect(self.__upload_barium_swallow_images)
        # Endoscopy / EGD
        self.ui.endoscopy_upload_button.clicked.connect(self.__upload_endoscopy_images)
        # Endoflip
        self.ui.endoflip_upload_button.clicked.connect(self.__upload_endoflip_file)

        # Therapy Buttons
        self.ui.add_botox_side_button.clicked.connect(self.__add_botox_injection)

        # Buttons of the Image Viewers
        self.ui.endoscopy_previous_button.clicked.connect(self.__endoscopy_previous_button_clicked)
        self.ui.endoscopy_next_button.clicked.connect(self.__endoscopy_next_button_clicked)
        self.ui.tbe_previous_button.clicked.connect(self.__barium_swallow_previous_button_clicked)
        self.ui.tbe_next_button.clicked.connect(self.__barium_swallow_next_button_clicked)

        menu_button = QAction("Info", self)
        menu_button.triggered.connect(self.__menu_button_clicked)
        self.ui.menubar.addAction(menu_button)

        self.__init_ui()

    # Function of the UI

    def __menu_button_clicked(self):
        """
        Info button callback. Shows information about file selection.
        """
        info_window = InfoWindow()
        info_window.show_file_selection_info()
        info_window.show()

    def __initialize_patient_model(self, filter_column: int = 6, filter_expression: str = '.*'):
        self.patients = self.patient_service.get_all_patients()
        self.patient_model = CustomPatientModel(self.patients)
        self.patient_proxyModel = QSortFilterProxyModel()
        self.patient_proxyModel.setSourceModel(self.patient_model)
        self.patient_proxyModel.setFilterKeyColumn(filter_column)
        self.patient_proxyModel.setFilterRegularExpression(filter_expression)

    def __init_ui(self, filter_column: int = 6, filter_expression: str = '.*'):
        self.__initialize_patient_model(filter_column, filter_expression)
        self.patient_tableView.setModel(self.patient_proxyModel)
        self.patient_tableView.setSortingEnabled(True)
        self.patient_tableView.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.patient_tableView.customContextMenuRequested.connect(self.__context_menu_patient)
        self.patient_tableView.verticalHeader().setDefaultSectionSize(30)
        self.patient_tableView.setColumnWidth(0, 50)
        self.patient_tableView.resizeColumnsToContents()
        self.patient_tableView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.patient_tableView.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.patient_tableView.clicked.connect(self.__select_patient)
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
        # Check if Patient alread exists
        if CheckDataExistence.patient_exists(self):
            # If Patient exists in database, ask user if their data should be updated
            if PopupWindow.update_confirmed():
                pat_dict = {'gender': self.ui.gender_dropdown.currentText(),
                            'ethnicity': self.ui.ethnicity_dropdown.currentText(),
                            'birth_year': self.ui.birthyear_calendar.date().toPyDate().year,
                            'year_first_diagnosis': self.ui.firstdiagnosis_calendar.date().toPyDate().year,
                            'year_first_symptoms': self.ui.firstsymptoms_calendar.date().toPyDate().year,
                            'center': self.ui.center_text.text()}
                # Validate Patients data
                patient_dict, null_values, error = DataValidation.validate_patient(pat_dict)
                if error:  # return if the user wants or needs to fill out additional data
                    return
                # update the patient in the database
                self.patient_service.update_patient(self.ui.patient_id_field.text(), pat_dict)
            else:  # return if the patient exists and should not be updated
                return
        else:  # the patient does not exist yet
            pat_dict = {
                'patient_id': self.ui.patient_id_field.text(),
                'gender': self.ui.gender_dropdown.currentText(),
                'ethnicity': self.ui.ethnicity_dropdown.currentText(),
                'birth_year': self.ui.birthyear_calendar.date().toPyDate().year,
                'year_first_diagnosis': self.ui.firstdiagnosis_calendar.date().toPyDate().year,
                'year_first_symptoms': self.ui.firstsymptoms_calendar.date().toPyDate().year,
                'center': self.ui.center_text.text()}
            # Validate the Patients data
            patient_dict, null_values, error = DataValidation.validate_patient(pat_dict)
            if error:  # return if the user wants or needs to fill out additional data
                return
            self.patient_service.create_patient(pat_dict)
        self.__init_ui()
        # Show the data of the selected patient in QTextEdit
        # pat_dict is needed again in case the patient was only updated
        pat_dict = {
            'patient_id': self.ui.patient_id_field.text(),
            'gender': self.ui.gender_dropdown.currentText(),
            'ethnicity': self.ui.ethnicity_dropdown.currentText(),
            'birth_year': self.ui.birthyear_calendar.date().toPyDate().year,
            'year_first_diagnosis': self.ui.firstdiagnosis_calendar.date().toPyDate().year,
            'year_first_symptoms': self.ui.firstsymptoms_calendar.date().toPyDate().year,
            'center': self.ui.center_text.text()}
        output = ""
        for key, value in pat_dict.items():
            output += f"{key}: {value}\n"
        self.ui.selected_patient_text_patientview.setText(output)
        self.ui.selected_patient_text_visitview.setText(output)
        self.ui.selected_patient_text_visitdataview.setText(output)
        # Set the text of the select visit to "please select a visit" until a visit for the patient is selected
        self.ui.selected_visit_text_visitview.setText("please select a visit")
        self.ui.selected_visit_text_visitdataview.setText("")
        # Set the text of the select previous therapy to "" until a previous therapy is selected
        self.ui.selected_therapy_text_patientview.setText("")

    def __patient_update_button_clicked(self):
        if not CheckDataExistence.patient_exists(self):
            if PopupWindow.add_confirmed():
                pat_dict = {'patient_id': self.ui.patient_id_field.text(),
                            'gender': self.ui.gender_dropdown.currentText(),
                            'ethnicity': self.ui.ethnicity_dropdown.currentText(),
                            'birth_year': self.ui.birthyear_calendar.date().toPyDate().year,
                            'year_first_diagnosis': self.ui.firstdiagnosis_calendar.date().toPyDate().year,
                            'year_first_symptoms': self.ui.firstsymptoms_calendar.date().toPyDate().year,
                            'center': self.ui.center_text.text()}
                # Validate the Patients data
                patient_dict, null_values, error = DataValidation.validate_patient(pat_dict)
                if error:  # return if the user wants or needs to fill out additional data
                    return
                self.patient_service.create_patient(pat_dict)
        else:  # if patient exists in database, patient data can be updated
            pat_dict = {
                'gender': self.ui.gender_dropdown.currentText(),
                'ethnicity': self.ui.ethnicity_dropdown.currentText(),
                'birth_year': self.ui.birthyear_calendar.date().toPyDate().year,
                'year_first_diagnosis': self.ui.firstdiagnosis_calendar.date().toPyDate().year,
                'year_first_symptoms': self.ui.firstsymptoms_calendar.date().toPyDate().year,
                'center': self.ui.center_text.text()}
            # Validate the Patients data
            patient_dict, null_values, error = DataValidation.validate_patient(pat_dict)
            if error:  # return if the user wants or needs to fill out additional data
                return
            self.patient_service.update_patient(self.ui.patient_id_field.text(), pat_dict)
        self.__init_ui()
        # Show the data of the selected patient in QTextEdit
        # pat_dict is needed again in case the patient was only updated
        pat_dict = {
            'patient_id': self.ui.patient_id_field.text(),
            'gender': self.ui.gender_dropdown.currentText(),
            'ethnicity': self.ui.ethnicity_dropdown.currentText(),
            'birth_year': self.ui.birthyear_calendar.date().toPyDate().year,
            'year_first_diagnosis': self.ui.firstdiagnosis_calendar.date().toPyDate().year,
            'year_first_symptoms': self.ui.firstsymptoms_calendar.date().toPyDate().year,
            'center': self.ui.center_text.text()}
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

    def __patient_delete_button_clicked(self):
        self.patient_service.delete_patient(
            self.selected_patient)
        self.__init_ui()
        self.__init_previous_therapies()
        self.__init_visits_of_patient()

        self.selected_patient = None
        self.ui.selected_patient_text_patientview.setText("please select a patient")
        self.ui.selected_patient_text_visitview.setText("please select a patient")
        self.ui.selected_patient_text_visitdataview.setText("please select a patient")
        # Set the text of the selected visit to "please select a visit"
        self.ui.selected_visit_text_visitview.setText("please select a visit")
        self.ui.selected_visit_text_visitdataview.setText("please select a visit")
        # Set the text of the select previous therapy to ""
        self.ui.selected_therapy_text_patientview.setText("")
        # Set the text for the manometry data
        self.ui.manometry_text.setText("")

        self.ui.visits.setEnabled(False)
        self.ui.eckardt_score.setEnabled(False)
        self.ui.visit_data.setEnabled(False)
        self.ui.previous_therapies.setEnabled(False)

    def __patient_id_filled(self):
        patient = self.patient_service.get_patient(
            self.ui.patient_id_field.text())

        if patient:
            if patient.birth_year is not None:
                self.ui.birthyear_calendar.setDate(QDate(patient.birth_year, 1, 1))
            else:
                self.ui.birthyear_calendar.setDate(QDate(config.min_value_year, 1, 1))

            if patient.year_first_diagnosis is not None:
                self.ui.firstdiagnosis_calendar.setDate(QDate(patient.year_first_diagnosis, 1, 1))
            else:
                self.ui.firstdiagnosis_calendar.setDate(QDate(config.min_value_year, 1, 1))

            if patient.year_first_symptoms is not None:
                self.ui.firstsymptoms_calendar.setDate(QDate(patient.year_first_symptoms, 1, 1))
            else:
                self.ui.firstsymptoms_calendar.setDate(QDate(config.min_value_year, 1, 1))

            if patient.gender is not None:
                if patient.gender == "male":
                    self.ui.gender_dropdown.setCurrentIndex(1)
                elif patient.gender == "female":
                    self.ui.gender_dropdown.setCurrentIndex(2)
                elif patient.gender == "divers":
                    self.ui.gender_dropdown.setCurrentIndex(3)
            else:
                self.ui.gender_dropdown.setCurrentIndex(0)

            if patient.ethnicity is not None:
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
                elif patient.ethnicity == "Other":
                    self.ui.ethnicity_dropdown.setCurrentIndex(6)
            else:
                self.ui.ethnicity_dropdown.setCurrentIndex(0)

            if patient.year_first_diagnosis is not None:
                self.ui.firstdiagnosis_calendar.setDate(QDate(config.min_value_year, 1, 1))
            else:
                self.ui.firstdiagnosis_calendar.setDate(QDate(config.min_value_year, 1, 1))

            if patient.year_first_symptoms is not None:
                self.ui.firstsymptoms_calendar.setDate(QDate(config.min_value_year, 1, 1))
            else:
                self.ui.firstsymptoms_calendar.setDate(QDate(config.min_value_year, 1, 1))

            if patient.center is not None:
                self.ui.center_text.setText(patient.center)

    def __select_patient(self):
        selected_indexes = self.patient_tableView.selectedIndexes()  # Get the indexes of all selected cells
        if selected_indexes:
            # Get the row number of the first selected index
            selected_row = selected_indexes[0].row()

            self.selected_patient = str(self.patient_tableView.model().index(selected_row, 0).data())

            # Access data for all columns in the selected row
            data = []
            for column in range(self.patient_tableView.model().columnCount()):
                index = self.patient_tableView.model().index(selected_row, column)
                data.append(str(index.data()))

            labels = self.patient_model.columns

            # Fetch the data of the selected patient to show it in various places of the app
            output = ""
            for key, value in zip(labels, data):
                output += f"{key}: {value}\n"

            self.__patient_selected(output)

            # Show the data of the selected patient in the drop-down/selection menu
            self.ui.patient_id_field.setText(
                str(self.patient_tableView.model().index(selected_row, 0).data()))
            self.__patient_id_filled()

    def __patient_selected(self, patient_data):
        self.ui.selected_patient_text_patientview.setText(patient_data)
        self.ui.selected_patient_text_visitview.setText(patient_data)
        self.ui.selected_patient_text_visitdataview.setText(patient_data)

        # Show the data of the selected patient in the other tabs
        self.__init_previous_therapies()
        self.__init_visits_of_patient()

        # Set the text of the select visit to "please select a visit" until a visit for the patient is selected
        self.ui.selected_visit_text_visitview.setText("please select a visit")
        self.ui.selected_visit_text_visitdataview.setText("please select a visit")
        # Set the text of the select previous therapy to "" until a previous therapy is selected
        self.ui.selected_therapy_text_patientview.setText("")
        # Set the text for the manometry data
        self.ui.manometry_text.setText("")

        self.ui.visits.setEnabled(True)
        self.ui.previous_therapies.setEnabled(True)
        self.ui.eckardt_score.setEnabled(False)
        self.ui.visit_data.setEnabled(False)

    def __patients_apply_filter(self):
        if self.ui.patient_id_radio.isChecked():
            filter_exp = '^' + self.ui.patient_id_field.text()  # all patient that start with this id are shown
            self.__init_ui(filter_column=0, filter_expression=filter_exp)
        if self.ui.birthyear_radio.isChecked():
            filter_exp = str(self.ui.birthyear_calendar.date().toPyDate().year)
            self.__init_ui(filter_column=3, filter_expression=filter_exp)
        if self.ui.gender_radio.isChecked():
            filter_exp = '^' + self.ui.gender_dropdown.currentText() + '$'
            self.__init_ui(filter_column=1, filter_expression=filter_exp)
        if self.ui.ethnicity_radio.isChecked():
            filter_exp = '^' + self.ui.ethnicity_dropdown.currentText() + '$'
            self.__init_ui(filter_column=2, filter_expression=filter_exp)
        if self.ui.firstdiagnosis_radio.isChecked():
            filter_exp = str(self.ui.firstdiagnosis_calendar.date().toPyDate().year)
            self.__init_ui(filter_column=4, filter_expression=filter_exp)
        if self.ui.firstsymptoms_radio.isChecked():
            filter_exp = str(self.ui.firstsymptoms_calendar.date().toPyDate().year)
            self.__init_ui(filter_column=5, filter_expression=filter_exp)
        if self.ui.center_radio.isChecked():
            filter_exp = '^' + self.ui.center_text.text()  # all patients whos centers start with this string
            self.__init_ui(filter_column=6, filter_expression=filter_exp)

    def __patients_reset_filter_button_clicked(self):
        self.__init_ui(filter_column=6, filter_expression='.*')
        # Uncheck Patient Id
        self.ui.patient_id_radio.setAutoExclusive(False)
        self.ui.patient_id_radio.setChecked(False)
        self.ui.patient_id_radio.setAutoExclusive(True)
        # Uncheck birthyear
        self.ui.birthyear_radio.setAutoExclusive(False)
        self.ui.birthyear_radio.setChecked(False)
        self.ui.birthyear_radio.setAutoExclusive(True)
        # Uncheck gender
        self.ui.gender_radio.setAutoExclusive(False)
        self.ui.gender_radio.setChecked(False)
        self.ui.gender_radio.setAutoExclusive(True)
        # Uncheck ethnicity
        self.ui.ethnicity_radio.setAutoExclusive(False)
        self.ui.ethnicity_radio.setChecked(False)
        self.ui.ethnicity_radio.setAutoExclusive(True)
        # Uncheck first diagnosis
        self.ui.firstdiagnosis_radio.setAutoExclusive(False)
        self.ui.firstdiagnosis_radio.setChecked(False)
        self.ui.firstdiagnosis_radio.setAutoExclusive(True)
        # Uncheck first symptoms
        self.ui.firstsymptoms_radio.setAutoExclusive(False)
        self.ui.firstsymptoms_radio.setChecked(False)
        self.ui.firstsymptoms_radio.setAutoExclusive(True)
        # Uncheck center
        self.ui.center_radio.setAutoExclusive(False)
        self.ui.center_radio.setChecked(False)
        self.ui.center_radio.setAutoExclusive(True)

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
        prev_therapy_dict = {
            'patient_id': self.selected_patient,
            'therapy': self.ui.therapy_dropdown.currentText(),
            'year': self.ui.therapy_calendar.date().toPyDate().year,
            'center': self.ui.center_previous_therapy_text.text()}
        patient_dict, null_values, error = DataValidation.validate_previous_therapy(prev_therapy_dict)
        if error:  # return if the user wants or needs to fill out additional data
            return
        self.previous_therapy_service.create_previous_therapy(prev_therapy_dict)
        self.__init_previous_therapies()

    def __previous_therapy_delete_button_clicked(self):
        self.previous_therapy_service.delete_previous_therapy(self.selected_previous_therapy)
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
        self.visits_tableView.clicked.connect(self.__select_visit)

    def __context_menu_visit(self):
        menu = QtWidgets.QMenu()
        if self.visits_tableView.selectedIndexes():
            remove_data = menu.addAction("Remove Data")
            remove_data.setIcon(QtGui.QIcon("./media/remove.png"))
            remove_data.triggered.connect(lambda: self.visits_model.removeRows(self.visits_tableView.currentIndex()))
        cursor = QtGui.QCursor()
        menu.exec(cursor.pos())

    def __visit_add_button_clicked(self):
        visit_dict = {'patient_id': self.selected_patient,
                      'year_of_visit': self.ui.year_of_visit_calendar.date().toPyDate().year,
                      'visit_type': self.ui.visit_type_dropdown.currentText(),
                      'therapy_type': self.ui.therapy_type_dropdown.currentText(),
                      'months_after_therapy': self.ui.months_after_therapy_spin.value()}
        visit_dict, null_values, error = DataValidation.validate_visit(visit_dict)
        if error:
            return
        self.visit_service.create_visit(visit_dict)
        self.__init_visits_of_patient()

    def __visit_delete_button_clicked(self):
        self.visit_service.delete_visit(
            self.selected_visit)
        self.__init_visits_of_patient()
        self.selected_visit = None
        self.ui.selected_visit_text_visitview.setText("please select a visit")
        self.ui.selected_visit_text_visitdataview.setText("please select a visit")
        self.ui.manometry_text.setText("")
        self.ui.eckardt_score.setEnabled(False)
        self.ui.visit_data.setEnabled(False)

    def __select_visit(self):
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

            self.selected_visit = str(self.visits_tableView.model().index(selected_row, 0).data())

            self.__visit_selected(output)

    def __visit_selected(self, visit_data):
        self.ui.selected_visit_text_visitview.setText(visit_data)
        self.ui.selected_visit_text_visitdataview.setText(visit_data)
        self.__init_manometry()

        visit = self.visit_service.get_visit(
            self.selected_visit)
        # Show the correct widget in the visitdata tab
        if visit:
            if visit.visit_type == "Follow-Up Diagnostic":
                self.ui.stackedWidget.setCurrentIndex(0)
            elif visit.visit_type == "Initial Diagnostic":
                self.ui.stackedWidget.setCurrentIndex(0)
            if visit.therapy_type == "Botox injection":
                self.ui.stackedWidget.setCurrentIndex(1)
            elif visit.therapy_type == "Pneumatic Dilitation":
                self.ui.stackedWidget.setCurrentIndex(2)
            elif visit.therapy_type == "POEM":
                self.ui.stackedWidget.setCurrentIndex(4)
            elif visit.therapy_type == "LHM":
                self.ui.stackedWidget.setCurrentIndex(3)

        if self.selected_visit:
            self.ui.eckardt_score.setEnabled(True)
            self.ui.eckardt_dysphagia_dropdown.setEnabled(True)
            self.ui.eckardt_retro_pain_dropdown.setEnabled(True)
            self.ui.eckardt_regurgitation_dropdown.setEnabled(True)
            self.ui.eckardt_weightloss_dropdown.setEnabled(True)
            self.ui.eckardt_totalscore_dropdown.setEnabled(True)
            self.ui.visit_data.setEnabled(True)

        if visit:
            endoscopy_images = self.endoscopy_file_service.get_endoscopy_images_for_visit(visit.visit_id)
            if endoscopy_images:
                self.endoscopy_pixmaps = endoscopy_images
                self.endoscopy_image_index = 0
                self.__load_endoscopy_image()

    def __validate_visit(self):
        if (
                1900 < self.ui.year_of_visit_calendar.date().toPyDate().year <= datetime.now().year
                and self.ui.visit_type_dropdown.currentText() != "---"
                and (
                self.ui.visit_type_dropdown.currentText() != "Therapy" or self.ui.therapy_type_dropdown.currentText() != "---")
                and (
                self.ui.therapy_type_dropdown.currentText() == "---" or self.ui.visit_type_dropdown.currentText() == "Therapy")
                and self.ui.months_after_therapy_spin.value() != -1
        ):
            return True
        return False

    def __add_eckardt_score_button_clicked(self):
        eckardt_dict = {'visit_id': self.selected_visit,
                        'dysphagia': self.ui.eckardt_dysphagia_dropdown.currentText(),
                        'retrosternal_pain': self.ui.eckardt_retro_pain_dropdown.currentText(),
                        'regurgitation': self.ui.eckardt_regurgitation_dropdown.currentText(),
                        'weightloss': self.ui.eckardt_weightloss_dropdown.currentText(),
                        'total_score': self.ui.eckardt_totalscore_dropdown.currentText()}
        if not self.__validate_eckardtscore():
            QMessageBox.warning(self, "Insufficient Data",
                                "Please fill out all data and make sure they are valid.")
        # check if an eckardt score is already in the DB for the selected visit
        elif self.eckardtscore_service.get_eckardtscores_for_visit(self.selected_visit):
            eckardt = self.eckardtscore_service.get_eckardtscores_for_visit(self.selected_visit)
            self.eckardtscore_service.update_eckardtscore(eckardt.eckardt_id, eckardt_dict)
        else:
            self.eckardtscore_service.create_eckardtscore(eckardt_dict)
        # ToDo ggf eine Anzeige für den EckardtScore einbauen

    def __delete_eckardt_score_button_clicked(self):
        self.eckardtscore_service.delete_eckardtscore_for_visit(
            self.selected_visit)

    def __validate_eckardtscore(self):
        if (
                self.ui.eckardt_dysphagia_dropdown.currentText() != '---' and
                self.ui.eckardt_retro_pain_dropdown.currentText() != '---' and
                self.ui.eckardt_regurgitation_dropdown.currentText() != '---' and
                self.ui.eckardt_weightloss_dropdown.currentText() != '---' and
                self.ui.eckardt_totalscore_dropdown.currentText() != '---'
        ):
            return True
        return False

    def __add_manometry(self):
        les_length = self.ui.manometry_upperboundary_les_spin.value() - self.ui.manometry_lowerboundary_les_spin.value()
        manometry_dict = {'visit_id': self.selected_visit,
                          'catheder_type': self.ui.manometry_cathedertype_dropdown.currentText(),
                          'patient_position': self.ui.manometry_patientposition_dropdown.currentText(),
                          'resting_pressure': self.ui.manometry_restingpressure_spin.value(),
                          'ipr4': self.ui.manometry_ipr4_spin.value(),
                          'dci': self.ui.manometry_dci_spin.value(),
                          'dl': self.ui.manometry_dl_spin.value(),
                          'ues_upper_boundary': self.ui.manometry_upperboundary_ues_spin.value(),
                          'ues_lower_boundary': self.ui.manometry_lowerboundary_ues_spin.value(),
                          'les_upper_boundary': self.ui.manometry_upperboundary_les_spin.value(),
                          'les_lower_boundary': self.ui.manometry_lowerboundary_les_spin.value(),
                          'les_length': les_length}
        manometry_dict, null_values, error = DataValidation.validate_visitdata(manometry_dict)

        if error:
            return

        if self.manometry_service.get_manometry_for_visit(self.selected_visit):
            manometry = self.manometry_service.get_manometry_for_visit(self.selected_visit)
            self.manometry_service.update_manometry(manometry.manometry_id, manometry_dict)
        else:
            self.manometry_service.create_manometry(manometry_dict)
        self.__init_manometry()

    def __add_barium_swallow(self):
        tbe_dict = {'visit_id': self.selected_visit,
                    'type_contrast_medium': self.ui.tbe_cm_dropdown.currentText(),
                    'amount_contrast_medium': self.ui.tbe_amount_cm_spin.value(),
                    'height_contast_medium_1min': self.ui.tbe_height_cm_1_spin.value(),
                    'height_contast_medium_2min': self.ui.tbe_height_cm_2_spin.value(),
                    'height_contast_medium_5min': self.ui.tbe_height_cm_5_spin.value(),
                    'width_contast_medium_1min': self.ui.tbe_width_cm_1_spin.value(),
                    'width_contast_medium_2min': self.ui.tbe_width_cm_2_spin.value(),
                    'width_contast_medium_5min': self.ui.tbe_width_cm_5_spin.value()}
        tbe_dict, null_values = DataValidation.validate_visitdata(tbe_dict)

        if null_values:
            null_message = "The following values are not set: " + ", ".join(
                null_values) + ". Do you want to set them to null/unknown?"
            reply = QMessageBox.question(self, 'Null Values Detected', null_message,
                                         QMessageBox.StandardButton.Yes |
                                         QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                return

    def __delete_manometry(self):
        self.manometry_service.delete_manometry_for_visit(
            self.selected_visit)
        self.__init_manometry()

    def __validate_manometry(self):
        if (
                self.ui.manometry_cathedertype_dropdown.currentText() != "---" and
                self.ui.manometry_patientposition_dropdown.currentText() != "---"
        ):
            return True
        return False

    def __init_manometry(self):
        manometry = self.manometry_service.get_manometry_for_visit(self.selected_visit)
        self.ui.manometry_text.setText(setText.set_text(manometry, "manometry data"))

    def __upload_manometry_file(self):
        """
        Manometry callback. Handles Manometry file selection.
        """
        manometry_exists = self.manometry_file_service.get_manometry_file_for_visit(self.selected_visit)
        if not manometry_exists or manometry_exists and self.to_update_for_visit("Manometry file"):
            filename, _ = QFileDialog.getOpenFileName(self, 'Select Manometry file', self.default_path,
                                                      "CSV (*.csv *.CSV)")
            if len(filename) > 0:
                process_and_upload_manometry_file(self.selected_visit, filename)
                self.ui.manometry_file_text.setText(filename)

    def __upload_barium_swallow_images(self):
        """
        Timed Barium Swallow (TBE) button callback. Handles TBE file selection.
        """
        # If TBE images are already uploaded in the database, images are deleted and updated with new images
        barium_swallow_exists = self.barium_swallow_file_service.get_barium_swallow_images_for_visit(
            self.selected_visit)
        if not barium_swallow_exists or barium_swallow_exists and self.to_update_for_visit("TBE Images"):
            self.barium_swallow_file_service.delete_barium_swallow_file_for_visit(self.selected_visit)

            filenames, _ = QFileDialog.getOpenFileNames(self, 'Select Files', self.default_path,
                                                        "Images (*.jpg *.JPG *.png *.PNG)")
            error = False

            for filename in filenames:
                match = re.search(r'(?P<time>[0-9]+)', filename)
                if not match:
                    error = True
                    QMessageBox.critical(self, "Unvalid Name", "The filename of the file '" + filename +
                                         "' does not contain the required time information, for example, '2.jpg' ")
                    break

            # if all images are named in the correct format, process and upload them
            if not error:
                process_and_upload_barium_swallow_images(self.selected_visit, filenames)
                self.ui.tbe_file_text.setText(str(len(filenames)) + " File(s) uploaded")
                # load the pixmaps of the images to make them viewable
                barium_swallow_images = self.barium_swallow_file_service.get_barium_swallow_images_for_visit(
                    self.selected_visit)
                if barium_swallow_images:
                    self.barium_swallow_pixmaps = barium_swallow_images
                    self.barium_swallow_image_index = 0
                    self.__load_barium_swallow_image()

    def __load_barium_swallow_image(self):
        # Load and display the current image
        if 0 <= self.barium_swallow_image_index < len(self.barium_swallow_pixmaps):
            scaled_pixmap = self.barium_swallow_pixmaps[self.barium_swallow_image_index].scaledToWidth(200)
            scaled_size = scaled_pixmap.size()
            self.ui.tbe_imageview.setPixmap(scaled_pixmap)
            self.ui.tbe_imageview.setFixedSize(scaled_size)

    def __barium_swallow_previous_button_clicked(self):
        # Show the previous image
        if self.barium_swallow_image_index > 0:
            self.barium_swallow_image_index -= 1
            self.__load_barium_swallow_image()

    def __barium_swallow_next_button_clicked(self):
        # Show the next image
        if self.barium_swallow_image_index < len(self.barium_swallow_pixmaps) - 1:
            self.barium_swallow_image_index += 1
            self.__load_barium_swallow_image()

    def __upload_endoscopy_images(self):
        """
        Endoscopy button callback. Handles endoscopy image selection.
        """
        # If endoscopy images are already uploaded in the database, images are deleted and updated with new images
        endoscopy_exists = self.endoscopy_file_service.get_endoscopy_images_for_visit(self.selected_visit)
        if not endoscopy_exists or endoscopy_exists and self.to_update_for_visit("Endoscopy Images"):
            self.endoscopy_file_service.delete_endoscopy_file_for_visit(self.selected_visit)

            filenames, _ = QFileDialog.getOpenFileNames(self, 'Select Files', self.default_path,
                                                        "Images (*.jpg *.JPG *.png *.PNG)")
            error = False

            for filename in filenames:
                match = re.search(r'_(?P<pos>[0-9]+)cm', filename)
                if not match:
                    error = True
                    QMessageBox.critical(self, "Unvalid Name", "The filename of the file '" + filename +
                                         "' does not contain the required positional information, for example, 'name_10cm.png' (Format: Underscore + Integer + cm)")
                    break

            # if all images have valid names, process and upload them
            if not error:
                process_and_upload_endoscopy_images(self.selected_visit, filenames)
                self.ui.endoscopy_textfield.setText(str(len(filenames)) + " File(s) uploaded")

                # load the pixmaps of the images to make them viewable
                endoscopy_images = self.endoscopy_file_service.get_endoscopy_images_for_visit(self.selected_visit)
                if endoscopy_images:
                    self.endoscopy_pixmaps = endoscopy_images
                    self.endoscopy_image_index = 0
                    self.__load_endoscopy_image()

    def to_update_for_visit(self, type_to_update: str):
        reply = QMessageBox.question(self, f'{type_to_update} already exists in the database.',
                                     f"Should the {type_to_update} for this visit be updated?",
                                     QMessageBox.StandardButton.Yes |
                                     QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            return True
        return False

    def __load_endoscopy_image(self):
        # Load and display the current image
        if 0 <= self.endoscopy_image_index < len(self.endoscopy_pixmaps):
            scaled_pixmap = self.endoscopy_pixmaps[self.endoscopy_image_index].scaledToWidth(200)
            scaled_size = scaled_pixmap.size()
            self.ui.endoscopy_imageview.setPixmap(scaled_pixmap)
            self.ui.endoscopy_imageview.setFixedSize(scaled_size)

    def __endoscopy_previous_button_clicked(self):
        # Show the previous image
        if self.endoscopy_image_index > 0:
            self.endoscopy_image_index -= 1
            self.__load_endoscopy_image()

    def __endoscopy_next_button_clicked(self):
        # Show the next image
        if self.endoscopy_image_index < len(self.endoscopy_pixmaps) - 1:
            self.endoscopy_image_index += 1
            self.__load_endoscopy_image()

    def __upload_endoflip_file(self):
        """
        EndoFLIP button callback. Handles EndoFLIP .xlsx file selection.
        """
        endoflip_exists = self.endoflip_file_service.get_endoflip_file_for_visit(self.selected_visit)
        if not endoflip_exists or endoflip_exists and self.to_update_for_visit("Endoflip file"):
            filename, _ = QFileDialog.getOpenFileName(self, 'Select file', self.default_path, "Excel (*.xlsx *.XLSX)")
            if len(filename) > 0:
                error = False
                try:
                    data_bytes, endoflip_screenshot = process_endoflip_xlsx(filename)
                except:
                    error = True
                if error or len(endoflip_screenshot['30']['aggregates']) != 4 or len(
                        endoflip_screenshot['40']['aggregates']) != 4:
                    print(error)
                    self.ui.endoflip_file_text.setText("")
                    QMessageBox.critical(self, "Invalid File", "Error: The file does not have the expected format.")
                else:
                    conduct_endoflip_file_upload(self.selected_visit, data_bytes, endoflip_screenshot)
                    self.ui.endoflip_file_text.setText(filename)
            self.default_path = os.path.dirname(filename)

    def __add_botox_injection(self):
        botox_dict = {'visit_id': self.selected_visit,
                      'botox_units': self.ui.botox_units_spin.value(),
                      'botox_height': self.ui.botox_height_spin.value()}
        botox_dict, null_values, error = DataValidation.validate_visitdata(botox_dict)

        if error:
            return

        self.botox_injection_service.create_botox_injection(botox_dict)
        self.__init_botox()

    def __init_botox(self):
        botox = self.botox_injection_service.get_botox_injections_for_visit(self.selected_visit)
        self.ui.botox_text.setText(setText.set_text_botox(botox, "Botox data"))


