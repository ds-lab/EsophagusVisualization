import os
import pickle
import re
from pathlib import Path
import config
from io import BytesIO

from PyQt6 import QtCore, uic, QtWidgets, QtGui
from PyQt6.QtGui import QAction, QPixmap
from PyQt6.QtWidgets import QMainWindow, QMessageBox, QFileDialog, QCompleter
from PyQt6.QtCore import Qt, QDate, QSortFilterProxyModel
from logic.patient_data import PatientData
from gui.master_window import MasterWindow
from gui.info_window import InfoWindow
from gui.set_textfields import setText
from gui.show_message import ShowMessage
from gui.xray_window_managment import ManageXrayWindows
from gui.visualization_window import VisualizationWindow
from gui.download_data_menu import DownloadData
from logic.datainput.endoflip_data_processing import process_endoflip_xlsx, conduct_endoflip_file_upload, \
    process_and_upload_endoflip_images
from logic.datainput.endoscopy_data_processing import process_and_upload_endoscopy_images
from logic.datainput.barium_swallow_data_processing import process_and_upload_barium_swallow_images
from logic.datainput.manometry_data_processing import process_and_upload_manometry_file
from logic.datainput.endosonography_data_processing import process_and_upload_endosonography_images
from logic.database import database
from logic.datainput.validate_input_data import DataValidation
from logic.datainput.check_data_existence import CheckDataExistence
from logic.services.patient_service import PatientService
from logic.services.visit_service import VisitService
from logic.services.eckardtscore_service import EckardtscoreService
from logic.services.manometry_service import ManometryService, ManometryFileService
from logic.services.previous_therapy_service import PreviousTherapyService
from logic.services.endoscopy_service import EndoscopyService, EndoscopyFileService
from logic.services.endoflip_service import EndoflipService, EndoflipFileService, EndoflipImageService
from logic.services.endosonography_service import EndosonographyImageService, EndosonographyVideoService
from logic.services.barium_swallow_service import BariumSwallowService, BariumSwallowFileService
from logic.services.botox_injection_service import BotoxInjectionService
from logic.services.complications_service import ComplicationsService
from logic.services.pneumatic_dilatation_service import PneumaticDilatationService
from logic.services.medication_service import MedicationService
from logic.services.lhm_service import LHMService
from logic.services.poem_service import POEMService
from logic.services.gerd_service import GerdService
from logic.services.reconstruction_service import ReconstructionService
from logic.database.pyqt_models import CustomPatientModel, CustomPreviousTherapyModel, CustomVisitsModel
from logic.visit_data import VisitData
from logic.visualization_data import VisualizationData
from logic.dataoutput.export_data import ExportData


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

        self.ui = uic.loadUi("./ui-files/data_window_design.ui", self)

        self.patient_tableView = self.ui.patient_tableView
        self.therapy_tableView = self.ui.therapy_tableView
        self.visits_tableView = self.ui.visits_tableView

        self.master_window = master_window
        self.db = database.get_db()
        self.engine = database.get_engine()

        self.patient_service = PatientService(self.db)
        self.previous_therapy_service = PreviousTherapyService(self.db)
        self.visit_service = VisitService(self.db)
        self.eckardtscore_service = EckardtscoreService(self.db)
        self.manometry_service = ManometryService(self.db)
        self.manometry_file_service = ManometryFileService(self.db)
        self.barium_swallow_service = BariumSwallowService(self.db)
        self.barium_swallow_file_service = BariumSwallowFileService(self.db)
        self.endoscopy_file_service = EndoscopyFileService(self.db)
        self.endoscopy_service = EndoscopyService(self.db)
        self.endoflip_service = EndoflipService(self.db)
        self.endoflip_file_service = EndoflipFileService(self.db)
        self.endoflip_image_service = EndoflipImageService(self.db)
        self.endosonography_image_service = EndosonographyImageService(self.db)
        self.endosonography_video_service = EndosonographyVideoService(self.db, self.engine)
        self.botox_injection_service = BotoxInjectionService(self.db)
        self.complications_service = ComplicationsService(self.db)
        self.pneumatic_dilatation_service = PneumaticDilatationService(self.db)
        self.lhm_service = LHMService(self.db)
        self.poem_service = POEMService(self.db)
        self.gerd_service = GerdService(self.db)
        self.medication_service = MedicationService(self.db)
        self.export_data = ExportData(self.db)
        self.reconstruction_service = ReconstructionService(self.db)

        # Data from DB have to be loaded into the correct data-structure for processing
        self.patient_data: PatientData = patient_data
        self.default_path = str(Path.home())
        self.import_filenames = []
        self.xray_filenames = []
        self.endoscopy_image_positions = []
        self.endoscopy_files = []
        self.endoflip_screenshot = None

        # Add Download Button to UI
        menu_button = QAction("Download Data", self)
        menu_button.triggered.connect(self.__download_data)
        self.ui.menubar.addAction(menu_button)

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
        self.ui.add_eckardt_score_button.clicked.connect(self.__add_eckardt_score)
        self.ui.delete_eckardt_score_button.clicked.connect(self.__delete_eckardt_score)
        # GERD
        self.ui.add_gerd_button.clicked.connect(self.__add_gerd)
        self.ui.delete_gerd_button.clicked.connect(self.__delete_gerd)
        # Medication
        self.ui.add_medication_button.clicked.connect(self.__add_medication)
        self.ui.delete_medication_button.clicked.connect(self.__delete_medication)
        # Create Visualization
        self.ui.visits_create_visualization_button.clicked.connect(self.__create_visualization)

        # Visit Data Tab
        # Manometry
        self.ui.add_manometry_button.clicked.connect(self.__add_manometry)
        self.ui.delete_manometry_button.clicked.connect(self.__delete_manometry)
        self.ui.manometry_file_upload_button.clicked.connect(self.__upload_manometry_file)
        # Barium Swallow / TBE
        self.ui.add_tbe_button.clicked.connect(self.__add_barium_swallow)
        self.ui.delete_tbe_button.clicked.connect(self.__delete_barium_swallow)
        self.ui.tbe_file_upload_button.clicked.connect(self.__upload_barium_swallow_images)
        # Endoscopy / EGD
        self.ui.add_egd_button.clicked.connect(self.__add_endoscopy)
        self.ui.delete_egd_button.clicked.connect(self.__delete_endoscopy)
        self.ui.egd_file_upload_button.clicked.connect(self.__upload_endoscopy_images)
        # Endoflip
        self.ui.add_endoflip_button.clicked.connect(self.__add_endoflip)
        self.ui.delete_endoflip_button.clicked.connect(self.__delete_endoflip)
        self.ui.endoflip_file_upload_button.clicked.connect(self.__upload_endoflip_files)
        self.ui.endoflip_image_upload_button.clicked.connect(self.__upload_endoflip_image)
        # Endosonography
        self.ui.endosono_image_upload_button.clicked.connect(self.__upload_endosonography_images)
        self.ui.endosono_video_upload_button.clicked.connect(self.__upload_endosonography_video)
        self.ui.endosono_video_download_button.clicked.connect(self.__download_endosonography_video)
        # Therapy Buttons
        # Botox
        self.ui.add_botox_side_button.clicked.connect(self.__add_botox_injection)
        self.ui.add_botox_button.clicked.connect(self.__add_botox_complications)
        self.ui.delete_botox_button.clicked.connect(self.__delete_botox)
        # Pneumatic Dilatation
        self.ui.add_pd_button.clicked.connect(self.__add_pneumatic_dilatation)
        self.ui.delete_pd_button.clicked.connect(self.__delete_pneumatic_dilatation)
        # LHM
        self.ui.add_lhm_button.clicked.connect(self.__add_lhm)
        self.ui.delete_lhm_button.clicked.connect(self.__delete_lhm)
        # POEM
        self.ui.add_poem_button.clicked.connect(self.__add_poem)
        self.ui.delete_poem_button.clicked.connect(self.__delete_poem)
        # Create Visualization
        self.ui.visitdata_create_visualization_button.clicked.connect(self.__create_visualization)

        # Buttons of the Image Viewers
        self.ui.endoscopy_previous_button.clicked.connect(self.__endoscopy_previous_button_clicked)
        self.ui.endoscopy_next_button.clicked.connect(self.__endoscopy_next_button_clicked)
        self.ui.tbe_previous_button.clicked.connect(self.__barium_swallow_previous_button_clicked)
        self.ui.tbe_next_button.clicked.connect(self.__barium_swallow_next_button_clicked)
        self.ui.endoflip_previous_button.clicked.connect(self.__endoflip_previous_button_clicked)
        self.ui.endoflip_next_button.clicked.connect(self.__endoflip_next_button_clicked)
        self.ui.endosono_previous_button.clicked.connect(self.__endosonography_previous_button_clicked)
        self.ui.endosono_next_button.clicked.connect(self.__endosonography_next_button_clicked)

        self.widget_names = {
            "Botox injection": 1,
            "Pneumatic Dilatation": 2,
            "LHM": 3,
            "POEM": 4
        }

        menu_button = QAction("Info", self)
        menu_button.triggered.connect(self.__menu_button_clicked)
        self.ui.menubar.addAction(menu_button)

        self.__init_ui()

    # Function of the UI

    def __menu_button_clicked(self):
        """
        Info button callback. Shows information about the data window
        """
        info_window = InfoWindow()
        info_window.show_data_window_info()
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

    def __patient_add_button_clicked(self):
        # Check if Patient alread exists
        if CheckDataExistence.patient_exists(self):
            # If Patient exists in database, ask user if their data should be updated
            if ShowMessage.update_confirmed():
                pat_dict = {'gender': self.ui.gender_dropdown.currentText(),
                            'ethnicity': self.ui.ethnicity_dropdown.currentText(),
                            'birth_year': self.ui.birthyear_calendar.date().toPyDate().year,
                            'year_first_diagnosis': self.ui.firstdiagnosis_calendar.date().toPyDate().year,
                            'year_first_symptoms': self.ui.firstsymptoms_calendar.date().toPyDate().year,
                            'center': self.ui.center_text.text()}
                # Validate Patients data
                patient_dict, error = DataValidation.validate_patient(pat_dict)
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
            patient_dict, error = DataValidation.validate_patient(pat_dict)
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
            if ShowMessage.add_confirmed():
                pat_dict = {'patient_id': self.ui.patient_id_field.text(),
                            'gender': self.ui.gender_dropdown.currentText(),
                            'ethnicity': self.ui.ethnicity_dropdown.currentText(),
                            'birth_year': self.ui.birthyear_calendar.date().toPyDate().year,
                            'year_first_diagnosis': self.ui.firstdiagnosis_calendar.date().toPyDate().year,
                            'year_first_symptoms': self.ui.firstsymptoms_calendar.date().toPyDate().year,
                            'center': self.ui.center_text.text()}
                # Validate the Patients data
                patient_dict, error = DataValidation.validate_patient(pat_dict)
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
            patient_dict, error = DataValidation.validate_patient(pat_dict)
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
        if ShowMessage.deletion_confirmed("patient"):
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
        self.therapy_tableView.verticalHeader().setDefaultSectionSize(30)
        self.therapy_tableView.setColumnWidth(0, 50)
        self.therapy_tableView.resizeColumnsToContents()
        self.therapy_tableView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.therapy_tableView.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.therapy_tableView.clicked.connect(self.__show_selected_previous_therapy_data)

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
        patient_dict, error = DataValidation.validate_previous_therapy(prev_therapy_dict)
        if error:  # return if the user wants or needs to fill out additional data
            return
        self.previous_therapy_service.create_previous_therapy(prev_therapy_dict)
        self.__init_previous_therapies()

    def __previous_therapy_delete_button_clicked(self):
        if ShowMessage.deletion_confirmed("previous therapies"):
            self.previous_therapy_service.delete_previous_therapy(self.selected_previous_therapy)
            self.__init_previous_therapies()
            self.selected_previous_therapy = None
            self.ui.selected_therapy_text_patientview.setText("")

    # Visit Functions
    def __init_visits_of_patient(self):
        self.visits_array = self.visit_service.get_visits_for_patient(self.selected_patient)
        self.visits_model = CustomVisitsModel(self.visits_array)
        self.visits_tableView.setModel(self.visits_model)
        self.visits_tableView.verticalHeader().setDefaultSectionSize(30)
        self.visits_tableView.setColumnWidth(0, 50)
        self.visits_tableView.resizeColumnsToContents()
        self.visits_tableView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.visits_tableView.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.visits_tableView.clicked.connect(self.__select_visit)

    def __visit_add_button_clicked(self):
        visit_dict = {'patient_id': self.selected_patient,
                      'year_of_visit': self.ui.year_of_visit_calendar.date().toPyDate().year,
                      'visit_type': self.ui.visit_type_dropdown.currentText(),
                      'therapy_type': self.ui.therapy_type_dropdown.currentText(),
                      'months_after_therapy': self.ui.months_after_therapy_spin.value()}
        visit_dict, error = DataValidation.validate_visit(visit_dict)
        if error:
            return
        self.visit_service.create_visit(visit_dict)
        self.__init_visits_of_patient()

    def __visit_delete_button_clicked(self):
        if ShowMessage.deletion_confirmed("visit"):
            self.visit_service.delete_visit(self.selected_visit)
            self.__init_visits_of_patient()
            self.selected_visit = None
            self.ui.selected_visit_text_visitview.setText("please select a visit")
            self.ui.selected_visit_text_visitdataview.setText("please select a visit")

            self.__init_manometry()
            self.__init_barium_swallow()
            self.__init_endoscopy()
            self.__init_endoflip()
            self.__init_botox()
            self.__init_pneumatic_dilatation()
            self.__init_lhm()
            self.__init_poem()
            self.__init_eckardt_score()
            self.__init_gerd()
            self.__init_medication()

        # Delete images
        # Barium Swallow
        self.ui.tbe_imageview.setText("No images are loaded")
        self.ui.tbe_imagedescription_text.setText("")
        # Endoscopy
        self.ui.endoscopy_imageview.setText("No images are loaded")
        self.ui.endoscopy_imagedescription_text.setText("")
        # EndoFlip
        self.ui.endoflip_imageview.setText("No images are loaded")
        self.ui.endoflip_imagedescription_text.setText("")
        # Endosonography
        self.ui.endosono_imageview.setText("No images are loaded")
        self.ui.endosono_imagedescription_text.setText("")

        # Disable Buttons until visit is selected
        self.ui.eckardt_score.setEnabled(False)
        self.ui.visit_data.setEnabled(False)
        self.ui.gerd.setEnabled(False)
        self.ui.medication.setEnabled(False)

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
        self.ui.eckardt_score.setEnabled(True)
        self.ui.visit_data.setEnabled(True)
        self.ui.visits_create_visualization_button.setEnabled(True)
        self.ui.gerd.setEnabled(True)
        self.ui.medication.setEnabled(True)

        self.ui.selected_visit_text_visitview.setText(visit_data)
        self.ui.selected_visit_text_visitdataview.setText(visit_data)

        self.__init_manometry()
        self.__init_barium_swallow()
        self.__init_endoscopy()
        self.__init_endoflip()
        self.__init_botox()
        self.__init_pneumatic_dilatation()
        self.__init_lhm()
        self.__init_poem()
        self.__init_eckardt_score()
        self.__init_gerd()
        self.__init_medication()

        visit = self.visit_service.get_visit(
            self.selected_visit)
        # Show the correct widget in the visitdata tab
        if visit:
            if visit.therapy_type in self.widget_names:
                widget_index = self.widget_names[visit.therapy_type]
                self.ui.stackedWidget.setCurrentIndex(widget_index)
            else:
                # No widget for therapy data input is shown
                self.ui.stackedWidget.setCurrentIndex(0)

        # Show images
        # Barium Swallow
        barium_swallow_images = self.barium_swallow_file_service.get_barium_swallow_images_for_visit(
            self.selected_visit)
        if barium_swallow_images:
            self.barium_swallow_pixmaps = barium_swallow_images
            self.barium_swallow_image_index = 0
        barium_swallow_minutes = self.barium_swallow_file_service.get_barium_swallow_minutes_for_visit(
            self.selected_visit)
        if barium_swallow_minutes:
            self.barium_swallow_minutes = barium_swallow_minutes
            self.__load_barium_swallow_image()
        # Endoscopy
        endoscopy_images = self.endoscopy_file_service.get_endoscopy_images_for_visit(self.selected_visit)
        if endoscopy_images:
            self.endoscopy_pixmaps = endoscopy_images
            self.endoscopy_image_index = 0
        endoscopy_positions = self.endoscopy_file_service.get_endoscopy_positions_for_visit(self.selected_visit)
        if endoscopy_positions:
            self.endoscopy_positions = endoscopy_positions
            self.__load_endoscopy_image()
        # EndoFlip
        endoflip_images = self.endoflip_image_service.get_endoflip_images_for_visit(self.selected_visit)
        if endoflip_images:
            self.endoflip_pixmaps = endoflip_images
            self.endoflip_image_index = 0
        endoflip_timepoints = self.endoflip_image_service.get_endoflip_timepoints_for_visit(self.selected_visit)
        if endoflip_timepoints:
            self.endoflip_timepoints = endoflip_timepoints
            self.__load_endoflip_image()
        # Endosonography
        endosono_images = self.endosonography_image_service.get_endosonography_images_for_visit(self.selected_visit)
        if endosono_images:
            self.endosono_pixmaps = endosono_images
            self.endosono_image_index = 0
        endosono_positions = self.endosonography_image_service.get_endosonography_positions_for_visit(
            self.selected_visit)
        if endosono_positions:
            self.endosono_positions = endosono_positions
            self.__load_endosonography_image()

    def __add_eckardt_score(self):
        eckardt = self.eckardtscore_service.get_eckardtscore_for_visit(self.selected_visit)
        if not eckardt or eckardt and ShowMessage.to_update_for_visit(
                "Eckardt Score"):
            eckardt_dict = {'visit_id': self.selected_visit,
                            'dysphagia': self.ui.eckardt_dysphagia_dropdown.currentText(),
                            'retrosternal_pain': self.ui.eckardt_retro_pain_dropdown.currentText(),
                            'regurgitation': self.ui.eckardt_regurgitation_dropdown.currentText(),
                            'weightloss': self.ui.eckardt_weightloss_dropdown.currentText(),
                            'total_score': self.ui.eckardt_totalscore_dropdown.currentText()}
            eckardt_dict, error = DataValidation.validate_eckardt(eckardt_dict)

            if error:
                return

            # check if an eckardt score is already in the DB for the selected visit
            if eckardt:
                self.eckardtscore_service.update_eckardtscore(eckardt.eckardt_id, eckardt_dict)
            else:
                self.eckardtscore_service.create_eckardtscore(eckardt_dict)
            self.__init_eckardt_score()

    def __init_eckardt_score(self):
        eckardt = self.eckardtscore_service.get_eckardtscore_for_visit(self.selected_visit)
        self.ui.eckardt_score_text.setText(setText.set_text(eckardt, "eckardt score"))

    def __delete_eckardt_score(self):
        if ShowMessage.deletion_confirmed("eckardt score"):
            self.eckardtscore_service.delete_eckardtscore_for_visit(
                self.selected_visit)
            self.__init_eckardt_score()

    def __add_gerd(self):
        gerd = self.gerd_service.get_gerd_for_visit(self.selected_visit)
        if not gerd or gerd and ShowMessage.to_update_for_visit("GERD"):
            heart_burn = None
            ppi_use = None
            if self.ui.heartburn_yes_ratio.isChecked():
                heart_burn = True
            elif self.ui.heartburn_no_ratio.isChecked():
                heart_burn = False
            if self.ui.ppi_yes_ratio.isChecked():
                ppi_use = True
            elif self.ui.ppi_no_ratio.isChecked():
                ppi_use = False
            gerd_dict = {'visit_id': self.selected_visit,
                         'grade': self.ui.gerd_reflux_dropdown.currentText(),
                         'heart_burn': heart_burn,
                         'ppi_use': ppi_use,
                         'acid_exposure_time': self.ui.gerd_acidexposure_spin.value()}
            gerd_dict, error = DataValidation.validate_gerd(gerd_dict)

            if error:
                return

            if gerd:
                self.gerd_service.update_gerd(gerd.gerd_id, gerd_dict)
            else:
                self.gerd_service.create_gerd(gerd_dict)
            self.__init_gerd()

    def __init_gerd(self):
        gerd = self.gerd_service.get_gerd_for_visit(self.selected_visit)
        self.ui.gerd_text.setText(setText.set_text(gerd, "GERD"))

    def __delete_gerd(self):
        if ShowMessage.deletion_confirmed("gerd score"):
            self.gerd_service.delete_gerd_for_visit(self.selected_visit)
            self.__init_gerd()

    def __add_medication(self):
        medication_dict = {'visit_id': self.selected_visit,
                           'medication_use': self.ui.medication_use_dropdown.currentText(),
                           'medication_name': self.ui.medication_name_text.text(),
                           'medication_dose': round(self.ui.medication_dose_spin.value(), 2)}
        medication_dict, error = DataValidation.validate_medication(medication_dict)
        if error:
            return
        self.medication_service.create_medication(medication_dict)

        self.__init_medication()

    def __init_medication(self):
        medication = self.medication_service.get_medications_for_visit(self.selected_visit)
        self.ui.medication_text.setText(setText.set_text_many(medication, "medication data"))

    def __delete_medication(self):
        if ShowMessage.deletion_confirmed("medications"):
            self.medication_service.delete_medications_for_visit(self.selected_visit)
            self.__init_medication()

    def __add_manometry(self):
        manometry = self.manometry_service.get_manometry_for_visit(self.selected_visit)
        if not manometry or manometry and ShowMessage.to_update_for_visit(
                "Timed Barium Swallow (TBE) data"):
            les_length = self.ui.manometry_upperboundary_les_spin.value() - self.ui.manometry_lowerboundary_les_spin.value()
            manometry_dict = {'visit_id': self.selected_visit,
                              'catheter_type': self.ui.manometry_cathedertype_dropdown.currentText(),
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
            manometry_dict, error = DataValidation.validate_visitdata(manometry_dict)

            if error:
                return

            if manometry:
                self.manometry_service.update_manometry(manometry.manometry_id, manometry_dict)
            else:
                self.manometry_service.create_manometry(manometry_dict)
            self.__init_manometry()

    def __delete_manometry(self):
        if ShowMessage.deletion_confirmed("manometry"):
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
        if not manometry_exists or manometry_exists and ShowMessage.to_update_for_visit("Manometry file"):
            filename, _ = QFileDialog.getOpenFileName(self, 'Select Manometry file', self.default_path,
                                                      "CSV (*.csv *.CSV)")
            if len(filename) > 0:
                process_and_upload_manometry_file(self.selected_visit, filename)
                self.ui.manometry_file_text.setText("Manometry File uploaded")

    def __add_barium_swallow(self):
        tbe = self.barium_swallow_service.get_barium_swallow_for_visit(self.selected_visit)
        if not tbe or tbe and ShowMessage.to_update_for_visit("Timed Barium Swallow (TBE) data"):
            tbe_dict = {'visit_id': self.selected_visit,
                        'type_contrast_medium': self.ui.tbe_cm_dropdown.currentText(),
                        'amount_contrast_medium': self.ui.tbe_amount_cm_spin.value(),
                        'height_contrast_medium_1min': self.ui.tbe_height_cm_1_spin.value(),
                        'height_contrast_medium_2min': self.ui.tbe_height_cm_2_spin.value(),
                        'height_contrast_medium_5min': self.ui.tbe_height_cm_5_spin.value(),
                        'width_contrast_medium_1min': self.ui.tbe_width_cm_1_spin.value(),
                        'width_contrast_medium_2min': self.ui.tbe_width_cm_2_spin.value(),
                        'width_contrast_medium_5min': self.ui.tbe_width_cm_5_spin.value()}
            tbe_dict, error = DataValidation.validate_visitdata(tbe_dict)

            if error:
                return

            if tbe:
                self.barium_swallow_service.update_barium_swallow(tbe.tbe_id, tbe_dict)
            else:
                self.barium_swallow_service.create_barium_swallow(tbe_dict)
            self.__init_barium_swallow()

    def __init_barium_swallow(self):
        barium_swallow = self.barium_swallow_service.get_barium_swallow_for_visit(self.selected_visit)
        self.ui.tbe_text.setText(setText.set_text(barium_swallow, "timed barium swallow data"))

    def __delete_barium_swallow(self):
        if ShowMessage.deletion_confirmed("barium swallow"):
            self.barium_swallow_service.delete_barium_swallow_for_visit(
                self.selected_visit)
            self.__init_barium_swallow()

    def __upload_barium_swallow_images(self):
        """
        Timed Barium Swallow (TBE) button callback. Handles TBE file selection.
        """
        # If TBE images are already uploaded in the database, images are deleted and updated with new images
        barium_swallow_exists = self.barium_swallow_file_service.get_barium_swallow_images_for_visit(
            self.selected_visit)
        if not barium_swallow_exists or barium_swallow_exists and ShowMessage.to_update_for_visit("TBE Images"):
            self.barium_swallow_file_service.delete_barium_swallow_files_for_visit(self.selected_visit)

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
                self.ui.tbe_file_text.setText(str(len(filenames)) + " Image(s) uploaded")
                # load the pixmaps of the images to make them viewable
                barium_swallow_images = self.barium_swallow_file_service.get_barium_swallow_images_for_visit(
                    self.selected_visit)
                barium_swallow_minutes = self.barium_swallow_file_service.get_barium_swallow_minutes_for_visit(
                    self.selected_visit)
                if barium_swallow_images:
                    self.barium_swallow_pixmaps = barium_swallow_images
                    self.barium_swallow_image_index = 0
                    self.barium_swallow_minutes = barium_swallow_minutes
                    self.__load_barium_swallow_image()

    def __load_barium_swallow_image(self):
        # Load and display the current image
        if 0 <= self.barium_swallow_image_index < len(self.barium_swallow_pixmaps):
            scaled_pixmap = self.barium_swallow_pixmaps[self.barium_swallow_image_index].scaledToWidth(200)
            scaled_size = scaled_pixmap.size()
            self.ui.tbe_imageview.setPixmap(scaled_pixmap)
            self.ui.tbe_imageview.setFixedSize(scaled_size)
            text = "Minute of image: " + str(self.barium_swallow_minutes[self.barium_swallow_image_index])
            self.ui.tbe_imagedescription_text.setText(text)

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

    def __add_endoscopy(self):
        egd = self.endoscopy_service.get_endoscopy_for_visit(self.selected_visit)
        if not egd or egd and ShowMessage.to_update_for_visit("Endoscopy (EGD) data"):
            egd_dict = {'visit_id': self.selected_visit,
                        'position_les': self.ui.egd_position_les_spin.value()}

            egd_dict, error = DataValidation.validate_visitdata(egd_dict)

            if error:
                return

            if egd:
                self.endoscopy_service.update_endoscopy(egd.egd_id, egd_dict)
            else:
                self.endoscopy_service.create_endoscopy(egd_dict)
            self.__init_endoscopy()

    def __init_endoscopy(self):
        endoscopy = self.endoscopy_service.get_endoscopy_for_visit(self.selected_visit)
        self.ui.egd_text.setText(setText.set_text(endoscopy, "endoscopy (EGD) data"))

    def __delete_endoscopy(self):
        if ShowMessage.deletion_confirmed("endoscopy"):
            self.endoscopy_service.delete_endoscopy_for_visit(
                self.selected_visit)
            self.__init_endoscopy()

    def __upload_endoscopy_images(self):
        """
        Endoscopy button callback. Handles endoscopy image selection.
        """
        # If endoscopy images are already uploaded in the database, images are deleted and updated with new images
        endoscopy_exists = self.endoscopy_file_service.get_endoscopy_images_for_visit(self.selected_visit)
        if not endoscopy_exists or endoscopy_exists and ShowMessage.to_update_for_visit("Endoscopy Images"):
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
                self.ui.egd_file_text.setText(str(len(filenames)) + " Image(s) uploaded")

                # load the pixmaps of the images to make them viewable
                endoscopy_images = self.endoscopy_file_service.get_endoscopy_images_for_visit(self.selected_visit)
                endoscopy_positions = self.endoscopy_file_service.get_endoscopy_positions_for_visit(self.selected_visit)
                if endoscopy_images:
                    self.endoscopy_pixmaps = endoscopy_images
                    self.endoscopy_image_index = 0
                    self.endoscopy_positions = endoscopy_positions
                    self.__load_endoscopy_image()

    def __load_endoscopy_image(self):
        # Load and display the current image
        if 0 <= self.endoscopy_image_index < len(self.endoscopy_pixmaps):
            scaled_pixmap = self.endoscopy_pixmaps[self.endoscopy_image_index].scaledToWidth(200)
            scaled_size = scaled_pixmap.size()
            self.ui.endoscopy_imageview.setPixmap(scaled_pixmap)
            self.ui.endoscopy_imageview.setFixedSize(scaled_size)
            text = "Image position: " + str(self.endoscopy_positions[self.endoscopy_image_index])
            self.ui.endoscopy_imagedescription_text.setText(text)

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

    def __add_endoflip(self):
        endoflip = self.endoflip_service.get_endoflip_for_visit(self.selected_visit)
        if not endoflip or endoflip and ShowMessage.to_update_for_visit("EndoFlip data"):
            endoflip_dict = {'visit_id': self.selected_visit,
                             'csa_before': self.ui.endflip_before_csa_spin.value(),
                             'di_before': self.ui.endflip_before_di_spin.value(),
                             'dmin_before': self.ui.endflip_before_dmin_spin.value(),
                             'ibp_before': self.ui.endflip_before_ibp_spin.value(),
                             'csa_during': self.ui.endflip_during_csa_spin.value(),
                             'di_during': self.ui.endflip_during_di_spin.value(),
                             'dmin_during': self.ui.endflip_during_dmin_spin.value(),
                             'ibp_during': self.ui.endflip_during_ibp_spin.value(),
                             'csa_after': self.ui.endflip_after_csa_spin.value(),
                             'di_after': self.ui.endflip_after_di_spin.value(),
                             'dmin_after': self.ui.endflip_after_dmin_spin.value(),
                             'ibp_after': self.ui.endflip_after_ibp_spin.value()}

            endoflip_dict, error = DataValidation.validate_visitdata(endoflip_dict)

            if error:
                return

            if endoflip:
                self.endoflip_service.update_endoflip(endoflip.endoflip_id, endoflip_dict)
            else:
                self.endoflip_service.create_endoflip(endoflip_dict)
            self.__init_endoflip()

    def __init_endoflip(self):
        endoflip = self.endoflip_service.get_endoflip_for_visit(self.selected_visit)
        self.ui.endoflip_text.setText(setText.set_text(endoflip, "EndoFlip data"))

    def __delete_endoflip(self):
        if ShowMessage.deletion_confirmed("EndoFlip"):
            self.endoflip_service.delete_endoflip_for_visit(self.selected_visit)
            self.__init_endoflip()

    def __upload_endoflip_files(self):
        """
        EndoFLIP-file button callback. Handles EndoFLIP .xlsx file selection.
        """
        endoflip_exists = self.endoflip_file_service.get_endoflip_files_for_visit(self.selected_visit)
        if not endoflip_exists or endoflip_exists and ShowMessage.to_update_for_visit("Endoflip files"):
            self.endoflip_file_service.delete_endoflip_file_for_visit(self.selected_visit)
            filenames, _ = QFileDialog.getOpenFileNames(self, 'Select file', self.default_path, "Excel (*.xlsx *.XLSX)")
            error = False
            for filename in filenames:
                match = re.search(r'(before|during|after)', filename)
                if not match:
                    error = True
                    QMessageBox.critical(self, "Unvalid Name", "The filename of the file '" + filename +
                                         "' does not contain the required time information ('before', 'during' or 'after'), for example, 'before.jpg' ")
                    break
            if not error:
                for filename in filenames:
                    if len(filename) > 0:
                        error = False
                        try:
                            data_bytes, endoflip_screenshot = process_endoflip_xlsx(filename)
                        except:
                            error = True
                        if error or len(endoflip_screenshot['30']['aggregates']) != 4 or len(
                                endoflip_screenshot['40']['aggregates']) != 4:
                            self.ui.endoflip_file_text.setText("")
                            QMessageBox.critical(self, "Invalid File",
                                                 "Error: The file does not have the expected format.")
                        else:
                            match = re.search(r'(before|during|after)', filename)
                            timepoint = match.group(0)
                            conduct_endoflip_file_upload(self.selected_visit, timepoint, data_bytes,
                                                         endoflip_screenshot)
                self.ui.endoflip_file_text.setText(str(len(filenames)) + " File(s) uploaded")
            self.default_path = os.path.dirname(filename)

    def __upload_endoflip_image(self):
        endoflip_exists = self.endoflip_file_service.get_endoflip_files_for_visit(self.selected_visit)
        if not endoflip_exists or endoflip_exists and ShowMessage.to_update_for_visit("Endoflip images"):
            self.endoflip_image_service.delete_endoflip_images_for_visit(self.selected_visit)
            filenames, _ = QFileDialog.getOpenFileNames(self, 'Select Files', self.default_path,
                                                        "Images (*.jpg *.JPG *.png *.PNG)")
            error = False
            for filename in filenames:
                match = re.search(r'(before|during|after)', filename)
                if not match:
                    error = True
                    QMessageBox.critical(self, "Unvalid Name", "The filename of the file '" + filename +
                                         "' does not contain the required time information, for example, '2.jpg' ")
                    break

            if not error:
                process_and_upload_endoflip_images(self.selected_visit, filenames)
                self.ui.endoflip_imagedescription_text.setText(str(len(filenames)) + " Image(s) uploaded")
                # load the pixmaps of the images to make them viewable
                endoflip_images = self.endoflip_image_service.get_endoflip_images_for_visit(
                    self.selected_visit)
                endoflip_timepoints = self.endoflip_image_service.get_endoflip_timepoints_for_visit(self.selected_visit)
                if endoflip_images:
                    self.endoflip_pixmaps = endoflip_images
                    self.endoflip_image_index = 0
                    self.endoflip_timepoints = endoflip_timepoints
                    self.__load_endoflip_image()

    def __load_endoflip_image(self):
        # Load and display the current image
        if 0 <= self.endoflip_image_index < len(self.endoflip_pixmaps):
            scaled_pixmap = self.endoflip_pixmaps[self.endoflip_image_index].scaledToWidth(200)
            scaled_size = scaled_pixmap.size()
            self.ui.endoflip_imageview.setPixmap(scaled_pixmap)
            self.ui.endoflip_imageview.setFixedSize(scaled_size)
            text = "Image timepoint: " + str(self.endoflip_timepoints[self.endoflip_image_index])
            self.ui.endoflip_imagedescription_text.setText(text)

    def __endoflip_previous_button_clicked(self):
        # Show the previous image
        if self.endoflip_image_index > 0:
            self.endoflip_image_index -= 1
            self.__load_endoflip_image()

    def __endoflip_next_button_clicked(self):
        # Show the next image
        if self.endoflip_image_index < len(self.endoflip_pixmaps) - 1:
            self.endoflip_image_index += 1
            self.__load_endoflip_image()

    def __upload_endosonography_images(self):
        """
        Endosonography button callback. Handles Endosonography file selection.
        """
        # If endosonography images are already uploaded in the database, images are deleted and updated with new images
        endosono_exists = self.endosonography_image_service.get_endosonography_images_for_visit(
            self.selected_visit)
        if not endosono_exists or endosono_exists and ShowMessage.to_update_for_visit("Endosonography Images"):
            self.endosonography_image_service.delete_endosonography_file_for_visit(self.selected_visit)

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

            # if all images are named in the correct format, process and upload them
            if not error:
                process_and_upload_endosonography_images(self.selected_visit, filenames)
                self.ui.endosono_images_text.setText(str(len(filenames)) + " Images(s) uploaded")
                # load the pixmaps of the images to make them viewable
                endosono_images = self.endosonography_image_service.get_endosonography_images_for_visit(
                    self.selected_visit)
                endosono_positions = self.endosonography_image_service.get_endosonography_positions_for_visit(
                    self.selected_visit)
                if endosono_images:
                    self.endosono_pixmaps = endosono_images
                    self.endosono_image_index = 0
                    self.endosono_positions = endosono_positions
                    self.__load_endosonography_image()

    def __load_endosonography_image(self):
        # Load and display the current image
        if 0 <= self.endosono_image_index < len(self.endosono_pixmaps):
            scaled_pixmap = self.endosono_pixmaps[self.endosono_image_index].scaledToWidth(200)
            scaled_size = scaled_pixmap.size()
            self.ui.endosono_imageview.setPixmap(scaled_pixmap)
            self.ui.endosono_imageview.setFixedSize(scaled_size)
            text = "Position of image: " + str(self.endosono_positions[self.endosono_image_index])
            self.ui.endosono_imagedescription_text.setText(text)

    def __endosonography_previous_button_clicked(self):
        # Show the previous image
        if self.endosono_image_index > 0:
            self.endosono_image_index -= 1
            self.__load_endosonography_image()

    def __endosonography_next_button_clicked(self):
        # Show the next image
        if self.endosono_image_index < len(self.endosono_pixmaps) - 1:
            self.endosono_image_index += 1
            self.__load_endosonography_image()

    def __upload_endosonography_video(self):
        endosono_exists = self.endosonography_video_service.get_endosonography_files_for_visit(self.selected_visit)
        if not endosono_exists or endosono_exists and ShowMessage.to_update_for_visit("Endosonography videos"):
            self.endosonography_video_service.delete_videos_for_visit(visit_id=self.selected_visit)
            filenames, _ = QFileDialog.getOpenFileNames(self, 'Select Files', self.default_path,
                                                        "Video Files (*.avi)")
            for filename in filenames:
                self.endosonography_video_service.save_video_for_visit(visit_id=self.selected_visit,
                                                                       video_file_path=filename)
            self.ui.endosono_videos_text.setText(str(len(filenames)) + " Videos(s) uploaded")

    def __download_endosonography_video(self):
        destination_directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if destination_directory:
            videos = self.endosonography_video_service.get_endosonography_videos_for_visit(visit_id=self.selected_visit)
            for i, video_data in enumerate(videos):
                path = os.path.join(destination_directory, f"{i}.mp4")
                with open(path, 'wb') as f:
                    f.write(video_data)

    def __add_botox_injection(self):
        botox_dict = {'visit_id': self.selected_visit,
                      'botox_units': self.ui.botox_units_spin.value(),
                      'botox_height': self.ui.botox_height_spin.value()}
        botox_dict, error = DataValidation.validate_visitdata(botox_dict)

        if error:
            return

        self.botox_injection_service.create_botox_injection(botox_dict)
        self.__init_botox()

    def __init_botox(self):
        botox = self.botox_injection_service.get_botox_injections_for_visit(self.selected_visit)
        complications = self.complications_service.get_complications_for_visit(self.selected_visit)
        botox_text = setText.set_text_many(botox, "Botox data")
        complications_text = setText.set_text(complications, "Complication data")
        text = botox_text + "\n" + "--- Complications ---\n" + complications_text
        self.ui.botox_text.setText(text)

    def __add_botox_complications(self):
        botox_complications = self.complications_service.get_complications_for_visit(self.selected_visit)
        if not botox_complications or botox_complications and ShowMessage.to_update_for_visit(
                "complications for the botox therapy"):
            botox_complications_dict = {'visit_id': self.selected_visit,
                                        'bleeding': self.ui.bleeding_botox.currentText(),
                                        'perforation': self.ui.perforation_botox.currentText(),
                                        'capnoperitoneum': self.ui.capnoperitoneum_botox.currentText(),
                                        'mucosal_tears': self.ui.mucusal_tears_botox.currentText(),
                                        'pneumothorax': self.ui.pneumothorax_botox.currentText(),
                                        'pneumomediastinum': self.ui.pneumomediastinum_botox.currentText(),
                                        'other_complication': self.ui.other_botox.currentText()}
            botox_complications_dict, error = DataValidation.validate_complications(botox_complications_dict)

            if error:
                return

            if botox_complications:
                self.complications_service.update_complications(botox_complications.complication_id,
                                                                botox_complications_dict)
            else:
                self.complications_service.create_complications(botox_complications_dict)
            self.__init_botox()

    def __delete_botox(self):
        if ShowMessage.deletion_confirmed("botox injections"):
            self.botox_injection_service.delete_botox_injections_for_visit(self.selected_visit)
            self.complications_service.delete_complications_for_visit(self.selected_visit)
            self.__init_botox()

    def __add_pneumatic_dilatation(self):
        pneumatic_dilatation = self.pneumatic_dilatation_service.get_pneumatic_dilatation_for_visit(self.selected_visit)
        if not pneumatic_dilatation or pneumatic_dilatation and ShowMessage.to_update_for_visit(
                "pneumatic dilatation data"):
            dilatation_dict = {'visit_id': self.selected_visit,
                               'balloon_volume': self.ui.pd_ballon_volume_dropdown.currentText(),
                               'quantity': self.ui.pd_quantity_spin.value()}
            dilatation_dict, error = DataValidation.validate_visitdata(dilatation_dict)

            if error:
                return

            if pneumatic_dilatation:
                self.pneumatic_dilatation_service.update_pneumatic_dilatation(
                    pneumatic_dilatation.pneumatic_dilatation_id, dilatation_dict)
            else:
                self.pneumatic_dilatation_service.create_pneumatic_dilatation(dilatation_dict)
        pd_complications = self.complications_service.get_complications_for_visit(self.selected_visit)
        if not pd_complications or pd_complications and ShowMessage.to_update_for_visit(
                "complications for the pneumatic dilatation therapy"):
            pd_complications_dict = {'visit_id': self.selected_visit,
                                     'bleeding': self.ui.bleeding_pd.currentText(),
                                     'perforation': self.ui.perforation_pd.currentText(),
                                     'capnoperitoneum': self.ui.capnoperitoneum_pd.currentText(),
                                     'mucosal_tears': self.ui.mucusal_tears_pd.currentText(),
                                     'pneumothorax': self.ui.pneumothorax_pd.currentText(),
                                     'pneumomediastinum': self.ui.pneumomediastinum_pd.currentText(),
                                     'other_complication': self.ui.other_pd.currentText()}
            pd_complications_dict, error = DataValidation.validate_complications(pd_complications_dict)

            if error:
                return

            if pd_complications:
                self.complications_service.update_complications(pd_complications.complication_id,
                                                                pd_complications_dict)
            else:
                self.complications_service.create_complications(pd_complications_dict)
        self.__init_pneumatic_dilatation()

    def __init_pneumatic_dilatation(self):
        pneumatic_dilatation = self.pneumatic_dilatation_service.get_pneumatic_dilatation_for_visit(self.selected_visit)
        complications = self.complications_service.get_complications_for_visit(self.selected_visit)
        pd_text = setText.set_text(pneumatic_dilatation, "Pneumatic dilatation data")
        complications_text = setText.set_text(complications, "Complication data")
        text = pd_text + "--- Complications ---\n" + complications_text
        self.ui.pd_text.setText(text)

    def __delete_pneumatic_dilatation(self):
        if ShowMessage.deletion_confirmed("pneumatic dilations"):
            self.pneumatic_dilatation_service.delete_pneumatic_dilatation_for_visit(self.selected_visit)
            self.complications_service.delete_complications_for_visit(self.selected_visit)
            self.__init_pneumatic_dilatation()

    def __add_lhm(self):
        lhm = self.lhm_service.get_lhm_for_visit(self.selected_visit)
        if not lhm or lhm and ShowMessage.to_update_for_visit("LHM data"):
            op_duration = (self.ui.lhm_time.time().hour() * 60) + self.ui.lhm_time.time().minute()
            lhm_dict = {'visit_id': self.selected_visit,
                        'op_duration': op_duration,
                        'length_myotomy': self.ui.lhm_length_spin.value(),
                        'fundoplicatio': self.ui.lhm_fundo_bool.isChecked(),
                        'type_fundoplicatio': self.ui.lhm_fundo_type_dropdown.currentText()}
            lhm_dict, error = DataValidation.validate_lhm(lhm_dict)

            if error:
                return

            if lhm:
                self.lhm_service.update_lhm(
                    lhm.lhm_id, lhm_dict)
            else:
                self.lhm_service.create_lhm(lhm_dict)
        lhm_complications = self.complications_service.get_complications_for_visit(self.selected_visit)
        if not lhm_complications or lhm_complications and ShowMessage.to_update_for_visit(
                "complications for the LHM therapy"):
            lhm_complications_dict = {'visit_id': self.selected_visit,
                                      'bleeding': self.ui.bleeding_lhm.currentText(),
                                      'perforation': self.ui.perforation_lhm.currentText(),
                                      'capnoperitoneum': self.ui.capnoperitoneum_lhm.currentText(),
                                      'mucosal_tears': self.ui.mucusal_tears_lhm.currentText(),
                                      'pneumothorax': self.ui.pneumothorax_lhm.currentText(),
                                      'pneumomediastinum': self.ui.pneumomediastinum_lhm.currentText(),
                                      'other_complication': self.ui.other_lhm.currentText()}
            lhm_complications_dict, error = DataValidation.validate_complications(lhm_complications_dict)

            if error:
                return

            if lhm_complications:
                self.complications_service.update_complications(lhm_complications.complication_id,
                                                                lhm_complications_dict)
            else:
                self.complications_service.create_complications(lhm_complications_dict)
        self.__init_lhm()

    def __init_lhm(self):
        lhm = self.lhm_service.get_lhm_for_visit(self.selected_visit)
        complications = self.complications_service.get_complications_for_visit(self.selected_visit)
        lhm_text = setText.set_text(lhm, "LHM data")
        complications_text = setText.set_text(complications, "Complication data")
        text = lhm_text + "--- Complications ---\n" + complications_text
        self.ui.lhm_text.setText(text)

    def __delete_lhm(self):
        if ShowMessage.deletion_confirmed("LHM"):
            self.lhm_service.delete_lhm_for_visit(self.selected_visit)
            self.complications_service.delete_complications_for_visit(self.selected_visit)
            self.__init_lhm()

    def __add_poem(self):
        poem = self.poem_service.get_poem_for_visit(self.selected_visit)
        if not poem or poem and ShowMessage.to_update_for_visit("POEM data"):
            procedure_duration = (self.ui.poem_time.time().hour() * 60) + self.ui.poem_time.time().minute()
            poem_dict = {'visit_id': self.selected_visit,
                         'procedure_duration': procedure_duration,
                         'height_mucosal_incision': self.ui.peom_incision_height_spin.value(),
                         'length_mucosal_incision': self.ui.peom_incision_length_spin.value(),
                         'length_submuscosal_tunnel': self.ui.peom_tunnel_length_spin.value(),
                         'localization_myotomy': self.ui.peom_localisation_dropdown.currentText(),
                         'length_tubular_myotomy': self.ui.peom_tubular_myotomy_length_spin.value(),
                         'length_gastric_myotomy': self.ui.poem_gastric_myotomy_length_spin.value()}
            poem_dict, error = DataValidation.validate_poem(poem_dict)

            if error:
                return

            if poem:
                self.poem_service.update_poem(
                    poem.poem_id, poem_dict)
            else:
                self.poem_service.create_poem(poem_dict)
        poem_complications = self.complications_service.get_complications_for_visit(self.selected_visit)
        if not poem_complications or poem_complications and ShowMessage.to_update_for_visit(
                "complications for the POEM therapy"):
            poem_complications_dict = {'visit_id': self.selected_visit,
                                       'bleeding': self.ui.bleeding_poem.currentText(),
                                       'perforation': self.ui.perforation_poem.currentText(),
                                       'capnoperitoneum': self.ui.capnoperitoneum_poem.currentText(),
                                       'mucosal_tears': self.ui.mucusal_tears_poem.currentText(),
                                       'pneumothorax': self.ui.pneumothorax_poem.currentText(),
                                       'pneumomediastinum': self.ui.pneumomediastinum_poem.currentText(),
                                       'other_complication': self.ui.other_poem.currentText()}
            poem_complications_dict, error = DataValidation.validate_complications(poem_complications_dict)

            if error:
                return

            if poem_complications:
                self.complications_service.update_complications(poem_complications.complication_id,
                                                                poem_complications_dict)
            else:
                self.complications_service.create_complications(poem_complications_dict)
        self.__init_poem()

    def __init_poem(self):
        poem = self.poem_service.get_poem_for_visit(self.selected_visit)
        complications = self.complications_service.get_complications_for_visit(self.selected_visit)
        poem_text = setText.set_text(poem, "LHM data")
        complications_text = setText.set_text(complications, "Complication data")
        text = poem_text + "--- Complications ---\n" + complications_text
        self.ui.poem_text.setText(text)

    def __delete_poem(self):
        if ShowMessage.deletion_confirmed("POEM"):
            self.poem_service.delete_poem_for_visit(self.selected_visit)
            self.complications_service.delete_complications_for_visit(self.selected_visit)
            self.__init_poem()

    def __create_visualization(self):
        barium_swallow_files = self.barium_swallow_file_service.get_barium_swallow_files_for_visit(
            self.selected_visit)
        manometry_file = self.manometry_file_service.get_manometry_file_for_visit(self.selected_visit)
        reconstruction = self.reconstruction_service.get_reconstruction_for_visit(self.selected_visit)

        patient = self.patient_service.get_patient(self.selected_patient)
        visit = self.visit_service.get_visit(self.selected_visit)
        visit_name = "[Visit_ID: " + str(
            self.selected_visit) + "]_" + patient.patient_id + "_" + visit.visit_type + "_" + str(visit.year_of_visit)

        if not reconstruction or reconstruction and not ShowMessage.load_saved_reconstruction():

            if barium_swallow_files is None or manometry_file is None:
                QMessageBox.critical(self, 'Missing Data', 'The Manometry file and at least one barium swallow image '
                                                           'are necessary for the 3D reconstruction.')
                return
            else:
                visit = VisitData(visit_name)

                for file in barium_swallow_files:
                    visualization_data = VisualizationData()
                    visualization_data.xray_minute = file.minute_of_picture
                    visualization_data.xray_file = BytesIO(file.file)
                    pressure_matrix = pickle.loads(manometry_file.pressure_matrix)
                    visualization_data.pressure_matrix = pressure_matrix

                    endoscopy = self.endoscopy_file_service.get_endoscopy_files_for_visit(self.selected_visit)
                    if endoscopy:
                        endoscopy_image_positions_cm = []
                        endoscopy_images = []
                        for endoscopy_file in endoscopy:
                            endoscopy_image_positions_cm.append(endoscopy_file.image_position)
                            endoscopy_images.append(BytesIO(endoscopy_file.file))

                        self.endoscopy_image_positions = endoscopy_image_positions_cm
                        self.endoscopy_files = endoscopy_images

                    visualization_data.endoscopy_image_positions_cm = self.endoscopy_image_positions
                    visualization_data.endoscopy_files = self.endoscopy_files

                    endoflip = self.endoflip_file_service.get_endoflip_files_for_visit(self.selected_visit)
                    if endoflip is not None:
                        # The first endoflip screenshot is used, because the app can only process one endoflip screenshot
                        visualization_data.endoflip_screenshot = pickle.loads(endoflip[0].screenshot)
                    else:
                        visualization_data.endoflip_screenshot = self.endoflip_screenshot

                    visit.add_visualization(visualization_data)

                ManageXrayWindows(self.master_window, visit, self.patient_data)

        else:
            print(f"reconstruction: {reconstruction}")
            reconstruction = pickle.loads(reconstruction.reconstruction_file)
            self.patient_data.add_visit(visit_name, reconstruction)

            visualization_window = VisualizationWindow(self.master_window, self.patient_data)
            self.master_window.switch_to(visualization_window)
            self.close()

    def __download_data(self):
        self.download_data = DownloadData()
        self.download_data.data_selected.connect(self.__handle_data_selected)
        self.download_data.show()

    def __handle_data_selected(self, selected_data, destination_file_path):
        data = self.export_data.get_data(selected_data)
        ExportData.export_csv(data, selected_data, destination_file_path)
